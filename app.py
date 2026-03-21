import os

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from models import db, User, Group, GroupMember, Expense, ExpenseSplit, Settlement, PasswordReset, Category, Comment, RecurringExpense
from datetime import datetime
import csv
import io

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///samplesplit.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["WTF_CSRF_ENABLED"] = True
app.config["TESTING"] = os.environ.get("TESTING", False)

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password1234"

db.init_app(app)
csrf = CSRFProtect(app)


def get_limiter_enabled():
    return not app.config.get("TESTING", False)


limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    enabled=get_limiter_enabled,
)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def calculate_balances(group_id):
    group = Group.query.get_or_404(group_id)
    members = [m.user for m in group.members]

    balances = {user.id: 0 for user in members}

    for expense in group.expenses:
        if expense.payer_id in balances:
            balances[expense.payer_id] += expense.amount
        for split in expense.splits:
            if split.user_id in balances:
                balances[split.user_id] -= split.amount_owed

    for settlement in group.settlements:
        if settlement.payer_id in balances:
            balances[settlement.payer_id] += settlement.amount
        if settlement.payee_id in balances:
            balances[settlement.payee_id] -= settlement.amount

    return balances


def simplify_debts(balances, members):
    creditors = []
    debtors = []

    for user_id, balance in balances.items():
        if balance > 0.01:
            creditors.append({"user_id": user_id, "amount": balance})
        elif balance < -0.01:
            debtors.append({"user_id": user_id, "amount": -balance})

    creditors.sort(key=lambda x: x["amount"], reverse=True)
    debtors.sort(key=lambda x: x["amount"], reverse=True)

    transfers = []
    i, j = 0, 0

    while i < len(creditors) and j < len(debtors):
        creditor = creditors[i]
        debtor = debtors[j]

        amount = min(creditor["amount"], debtor["amount"])

        if amount > 0.01:
            transfers.append({"from": debtor["user_id"], "to": creditor["user_id"], "amount": round(amount, 2)})

        creditor["amount"] -= amount
        debtor["amount"] -= amount

        if creditor["amount"] < 0.01:
            i += 1
        if debtor["amount"] < 0.01:
            j += 1

    return transfers


@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = []

        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters.")
        if not email or "@" not in email:
            errors.append("Please enter a valid email address.")
        if not password or len(password) < 4:
            errors.append("Password must be at least 4 characters.")
        if password != confirm_password:
            errors.append("Passwords do not match.")
        if User.query.filter_by(username=username).first():
            errors.append("Username already taken.")
        if User.query.filter_by(email=email).first():
            errors.append("Email already registered.")

        if errors:
            for error in errors:
                flash(error, "error")
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("3 per minute")
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()

        if identifier:
            user = User.query.filter_by(username=identifier).first()
            if not user:
                user = User.query.filter_by(email=identifier).first()

            if user:
                existing = PasswordReset.query.filter_by(user_id=user.id, status="pending").first()
                if existing:
                    flash("A reset request is already pending for this account.", "info")
                else:
                    reset_request = PasswordReset(user_id=user.id)
                    db.session.add(reset_request)
                    db.session.commit()
                    flash("Password reset request submitted. Please contact an administrator.", "success")
            else:
                flash("If an account exists with that username or email, a reset request has been submitted.", "info")

        return redirect(url_for("login"))

    return render_template("forgot_password.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/extend-session", methods=["POST"])
@login_required
def extend_session():
    from flask import jsonify

    return jsonify({"status": "ok"})


@app.route("/dashboard")
@login_required
def dashboard():
    groups = current_user.get_groups()
    group_balances = {}

    for group in groups:
        balances = calculate_balances(group.id)
        user_balance = balances.get(current_user.id, 0)
        group_balances[group.id] = round(user_balance, 2)

    return render_template("dashboard.html", groups=groups, group_balances=group_balances)


@app.route("/group/create", methods=["GET", "POST"])
@login_required
def create_group():
    if request.method == "POST":
        name = request.form.get("name", "").strip()

        if not name:
            flash("Group name is required.", "error")
            return render_template("create_group.html")

        invite_code = Group.generate_invite_code()
        group = Group(name=name, invite_code=invite_code, created_by_id=current_user.id)
        db.session.add(group)
        db.session.flush()

        member = GroupMember(user_id=current_user.id, group_id=group.id)
        db.session.add(member)
        db.session.commit()

        flash(f'Group "{name}" created! Invite code: {invite_code}', "success")
        return redirect(url_for("group", group_id=group.id))

    return render_template("create_group.html")


@app.route("/group/join", methods=["GET", "POST"])
@login_required
def join_group():
    if request.method == "POST":
        invite_code = request.form.get("invite_code", "").strip()

        if not invite_code or len(invite_code) != 6:
            flash("Please enter a valid 6-digit invite code.", "error")
            return render_template("join_group.html")

        group = Group.query.filter_by(invite_code=invite_code).first()

        if not group:
            flash("Invalid invite code. Please check and try again.", "error")
            return render_template("join_group.html")

        existing = GroupMember.query.filter_by(user_id=current_user.id, group_id=group.id).first()
        if existing:
            flash("You are already a member of this group.", "info")
            return redirect(url_for("group", group_id=group.id))

        member = GroupMember(user_id=current_user.id, group_id=group.id)
        db.session.add(member)
        db.session.commit()

        flash(f'Successfully joined "{group.name}"!', "success")
        return redirect(url_for("group", group_id=group.id))

    return render_template("join_group.html")


@app.route("/group/<int:group_id>")
@app.route("/group/<int:group_id>")
@login_required
def group(group_id):
    group_obj = Group.query.get_or_404(group_id)

    membership = GroupMember.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    if not membership:
        flash("You are not a member of this group.", "error")
        return redirect(url_for("dashboard"))

    members = [m.user for m in group_obj.members]
    balances = calculate_balances(group_id)
    simplified = simplify_debts(balances, members)

    member_balances = {}
    for user in members:
        member_balances[user.id] = {"user": user, "balance": round(balances.get(user.id, 0), 2)}

    search_query = request.args.get("q", "").strip()
    category_filter = request.args.get("category", "").strip()
    sort_by = request.args.get("sort", "date")

    expenses = Expense.query.filter_by(group_id=group_id)
    if search_query:
        expenses = expenses.filter(Expense.description.ilike(f"%{search_query}%"))
    if category_filter:
        try:
            cat_id = int(category_filter)
            expenses = expenses.filter(Expense.category_id == cat_id)
        except ValueError:
            pass

    if sort_by == "amount_desc":
        expenses = expenses.order_by(Expense.amount.desc())
    elif sort_by == "amount_asc":
        expenses = expenses.order_by(Expense.amount.asc())
    elif sort_by == "category":
        expenses = expenses.order_by(Expense.category_id.desc())
    else:
        expenses = expenses.order_by(Expense.created_at.desc())

    expenses = expenses.all()

    settlements = Settlement.query.filter_by(group_id=group_id).order_by(Settlement.created_at.desc()).limit(10).all()

    all_transactions = []
    for expense in expenses:
        all_transactions.append({"type": "expense", "data": expense, "created_at": expense.created_at})
    for settlement in settlements:
        all_transactions.append({"type": "settlement", "data": settlement, "created_at": settlement.created_at})
    all_transactions.sort(key=lambda x: x["created_at"], reverse=True)

    user_balance = balances.get(current_user.id, 0)

    categories = Category.query.filter_by(group_id=group_id).order_by(Category.name).all()
    category_summary = {}
    for cat in categories:
        total = sum(e.amount for e in cat.expenses if e.group_id == group_id)
        if total > 0:
            category_summary[cat.id] = {"category": cat, "total": round(total, 2)}

    return render_template(
        "group.html",
        group=group_obj,
        members=members,
        member_balances=member_balances,
        simplified=simplified,
        transactions=all_transactions,
        user_balance=round(user_balance, 2),
        search_query=search_query,
        category_filter=category_filter,
        sort_by=sort_by,
        categories=categories,
        category_summary=category_summary,
    )


@app.route("/group/<int:group_id>/edit", methods=["POST"])
@login_required
def edit_group(group_id):
    group_obj = Group.query.get_or_404(group_id)

    membership = GroupMember.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    if not membership:
        flash("You are not a member of this group.", "error")
        return redirect(url_for("dashboard"))

    new_name = request.form.get("name", "").strip()
    if new_name:
        group_obj.name = new_name
        db.session.commit()
        flash(f'Group renamed to "{new_name}"', "success")

    return redirect(url_for("group", group_id=group_id))


@app.route("/group/<int:group_id>/leave", methods=["POST"])
@login_required
def leave_group(group_id):
    group_obj = Group.query.get_or_404(group_id)

    membership = GroupMember.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    if not membership:
        flash("You are not a member of this group.", "error")
        return redirect(url_for("dashboard"))

    db.session.delete(membership)
    db.session.commit()
    flash(f'You left "{group_obj.name}"', "info")
    return redirect(url_for("dashboard"))


@app.route("/group/<int:group_id>/remove/<int:user_id>", methods=["POST"])
@login_required
def remove_member(group_id, user_id):
    group_obj = Group.query.get_or_404(group_id)

    if group_obj.created_by_id != current_user.id:
        flash("Only the group creator can remove members.", "error")
        return redirect(url_for("group", group_id=group_id))

    if user_id == current_user.id:
        flash("You cannot remove yourself. Use 'Leave Group' instead.", "error")
        return redirect(url_for("group", group_id=group_id))

    membership = GroupMember.query.filter_by(user_id=user_id, group_id=group_id).first()
    if not membership:
        flash("Member not found in this group.", "error")
        return redirect(url_for("group", group_id=group_id))

    removed_user = User.query.get(user_id)
    db.session.delete(membership)
    db.session.commit()
    flash(f'{removed_user.username} has been removed from the group.', "info")
    return redirect(url_for("group", group_id=group_id))


@app.route("/group/<int:group_id>/categories")
@login_required
def manage_categories(group_id):
    group_obj = Group.query.get_or_404(group_id)

    membership = GroupMember.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    if not membership:
        flash("You are not a member of this group.", "error")
        return redirect(url_for("dashboard"))

    categories = Category.query.filter_by(group_id=group_id).order_by(Category.name).all()

    return render_template("manage_categories.html", group=group_obj, categories=categories)


@app.route("/group/<int:group_id>/category", methods=["POST"])
@login_required
def add_category(group_id):
    group_obj = Group.query.get_or_404(group_id)

    membership = GroupMember.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    if not membership:
        flash("You are not a member of this group.", "error")
        return redirect(url_for("dashboard"))

    name = request.form.get("name", "").strip()
    icon = request.form.get("icon", "tag").strip()
    color = request.form.get("color", "#6b7280").strip()

    if not name:
        flash("Category name is required.", "error")
        return redirect(url_for("manage_categories", group_id=group_id))

    existing = Category.query.filter_by(group_id=group_id, name=name).first()
    if existing:
        flash(f'Category "{name}" already exists.', "error")
        return redirect(url_for("manage_categories", group_id=group_id))

    category = Category(group_id=group_id, name=name, icon=icon, color=color)
    db.session.add(category)
    db.session.commit()

    flash(f'Category "{name}" created!', "success")
    return redirect(url_for("manage_categories", group_id=group_id))


@app.route("/group/<int:group_id>/category/<int:category_id>/delete", methods=["POST"])
@login_required
def delete_category(group_id, category_id):
    group_obj = Group.query.get_or_404(group_id)

    membership = GroupMember.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    if not membership:
        flash("You are not a member of this group.", "error")
        return redirect(url_for("dashboard"))

    category = Category.query.get_or_404(category_id)
    if category.group_id != group_id:
        flash("Category not found in this group.", "error")
        return redirect(url_for("manage_categories", group_id=group_id))

    Expense.query.filter_by(category_id=category_id).update({Expense.category_id: None})
    db.session.delete(category)
    db.session.commit()

    flash(f'Category "{category.name}" deleted.', "success")
    return redirect(url_for("manage_categories", group_id=group_id))


@app.route("/group/<int:group_id>/expense", methods=["GET", "POST"])
@login_required
def add_expense(group_id):
    group_obj = Group.query.get_or_404(group_id)

    membership = GroupMember.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    if not membership:
        flash("You are not a member of this group.", "error")
        return redirect(url_for("dashboard"))

    members = [m.user for m in group_obj.members]

    if request.method == "POST":
        amount = request.form.get("amount", type=float)
        description = request.form.get("description", "").strip()
        payer_id = request.form.get("payer_id", type=int)
        selected_members = request.form.getlist("members")
        expense_date_str = request.form.get("expense_date", "")
        split_type = request.form.get("split_type", "equal")
        category_id = request.form.get("category_id", type=int)
        tags = request.form.get("tags", "").strip()

        errors = []

        if not amount or amount <= 0:
            errors.append("Please enter a valid amount.")
        if not payer_id:
            errors.append("Please select who paid.")
        if not selected_members:
            errors.append("Please select at least one person to split with.")
        if payer_id and int(payer_id) not in [m.id for m in members]:
            errors.append("Invalid payer selected.")
        for mid in selected_members:
            if int(mid) not in [m.id for m in members]:
                errors.append("Invalid member selected.")

        expense_date = datetime.utcnow().date()
        if expense_date_str:
            try:
                expense_date = datetime.strptime(expense_date_str, "%Y-%m-%d").date()
            except ValueError:
                errors.append("Invalid date format.")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("add_expense.html", group=group_obj, members=members, categories=group_obj.categories)
        else:
            splits = []

            if split_type == "equal":
                split_amount = amount / len(selected_members)
                for member_id in selected_members:
                    splits.append((int(member_id), round(split_amount, 2)))

            elif split_type == "percentage":
                for member_id in selected_members:
                    pct_key = f"percentage_{member_id}"
                    pct = request.form.get(pct_key, type=float, default=0)
                    split_amount = (pct / 100) * amount
                    splits.append((int(member_id), round(split_amount, 2)))

                total_pct = sum(float(request.form.get(f"percentage_{mid}", 0)) for mid in selected_members)
                if abs(total_pct - 100) > 0.1:
                    flash(f"Percentages must total 100% (currently {total_pct:.1f}%)", "error")
                    return render_template("add_expense.html", group=group_obj, members=members, categories=group_obj.categories)

            elif split_type == "exact":
                remaining = amount
                last_member = None

                for member_id in selected_members:
                    amt_key = f"amount_{member_id}"
                    split_amount = request.form.get(amt_key, type=float, default=0)
                    splits.append((int(member_id), split_amount))
                    remaining -= split_amount
                    last_member = member_id

                if abs(remaining) > 0.01:
                    if last_member and abs(remaining) < amount:
                        splits = [
                            (
                                mid,
                                (
                                    float(request.form.get(f"amount_{mid}", 0))
                                    if mid != last_member
                                    else round(float(request.form.get(f"amount_{mid}", 0)) + remaining, 2)
                                ),
                            )
                            for mid in selected_members
                        ]
                    else:
                        flash(f"Amounts must total ₹{amount:.2f}", "error")
                        return render_template("add_expense.html", group=group_obj, members=members, categories=group_obj.categories)

            expense = Expense(
                group_id=group_id,
                payer_id=payer_id,
                description=description or "Expense",
                amount=amount,
                expense_date=expense_date,
                category_id=category_id if category_id else None,
                tags=tags,
            )
            db.session.add(expense)
            db.session.flush()

            for user_id, amount_owed in splits:
                split = ExpenseSplit(expense_id=expense.id, user_id=user_id, amount_owed=amount_owed)
                db.session.add(split)

            db.session.commit()
            flash("Expense added successfully!", "success")
            return redirect(url_for("group", group_id=group_id))

    return render_template("add_expense.html", group=group_obj, members=members, categories=group_obj.categories)


@app.route("/group/<int:group_id>/expense/<int:expense_id>/delete", methods=["POST"])
@login_required
def delete_expense(group_id, expense_id):
    expense = Expense.query.get_or_404(expense_id)

    if expense.payer_id != current_user.id:
        flash("Only the person who created this expense can delete it.", "error")
        return redirect(url_for("group", group_id=group_id))

    db.session.delete(expense)
    db.session.commit()
    flash("Expense deleted.", "success")
    return redirect(url_for("group", group_id=group_id))


@app.route("/group/<int:group_id>/expense/<int:expense_id>/comment", methods=["POST"])
@login_required
def add_comment(group_id, expense_id):
    group_obj = Group.query.get_or_404(group_id)

    membership = GroupMember.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    if not membership:
        flash("You are not a member of this group.", "error")
        return redirect(url_for("dashboard"))

    expense = Expense.query.get_or_404(expense_id)
    if expense.group_id != group_id:
        flash("Expense not found in this group.", "error")
        return redirect(url_for("group", group_id=group_id))

    content = request.form.get("content", "").strip()
    if not content:
        flash("Comment cannot be empty.", "error")
        return redirect(url_for("group", group_id=group_id))

    comment = Comment(expense_id=expense_id, user_id=current_user.id, content=content)
    db.session.add(comment)
    db.session.commit()
    flash("Comment added.", "success")
    return redirect(url_for("group", group_id=group_id))


@app.route("/group/<int:group_id>/expense/<int:expense_id>/receipt", methods=["POST"])
@login_required
def upload_receipt(group_id, expense_id):
    membership = GroupMember.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    if not membership:
        flash("You are not a member of this group.", "error")
        return redirect(url_for("dashboard"))

    expense = Expense.query.get_or_404(expense_id)
    if expense.group_id != group_id:
        flash("Expense not found in this group.", "error")
        return redirect(url_for("group", group_id=group_id))

    if expense.payer_id != current_user.id:
        flash("Only the expense creator can upload receipts.", "error")
        return redirect(url_for("group", group_id=group_id))

    if "receipt" not in request.files:
        flash("No file selected.", "error")
        return redirect(url_for("group", group_id=group_id))

    file = request.files["receipt"]
    if file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("group", group_id=group_id))

    if file:
        import os
        import uuid
        from werkzeug.utils import secure_filename

        upload_dir = os.path.join(app.root_path, "static", "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        ext = os.path.splitext(secure_filename(file.filename))[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)

        expense.receipt_url = f"/static/uploads/{filename}"
        db.session.commit()
        flash("Receipt uploaded.", "success")

    return redirect(url_for("group", group_id=group_id))


@app.route("/group/<int:group_id>/recurring", methods=["GET", "POST"])
@login_required
def manage_recurring(group_id):
    group_obj = Group.query.get_or_404(group_id)

    membership = GroupMember.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    if not membership:
        flash("You are not a member of this group.", "error")
        return redirect(url_for("dashboard"))

    members = [m.user for m in group_obj.members]

    if request.method == "POST":
        action = request.form.get("action")

        if action == "create":
            amount = request.form.get("amount", type=float)
            description = request.form.get("description", "").strip()
            payer_id = request.form.get("payer_id", type=int)
            frequency = request.form.get("frequency", "monthly")
            category_id = request.form.get("category_id", type=int)
            tags = request.form.get("tags", "").strip()

            if not amount or amount <= 0:
                flash("Please enter a valid amount.", "error")
                return render_template("recurring.html", group=group_obj, members=members, recurring=group_obj.recurring_expenses)

            recurring = RecurringExpense(
                group_id=group_id,
                payer_id=payer_id,
                description=description or "Recurring expense",
                amount=amount,
                frequency=frequency,
                category_id=category_id if category_id else None,
                tags=tags,
            )
            db.session.add(recurring)
            db.session.commit()
            flash("Recurring expense created!", "success")

        elif action == "toggle":
            recurring_id = request.form.get("recurring_id", type=int)
            recurring = RecurringExpense.query.get_or_404(recurring_id)
            if recurring.group_id == group_id:
                recurring.is_active = not recurring.is_active
                db.session.commit()
                flash(f"Recurring expense {'enabled' if recurring.is_active else 'disabled'}.", "info")

        elif action == "delete":
            recurring_id = request.form.get("recurring_id", type=int)
            recurring = RecurringExpense.query.get_or_404(recurring_id)
            if recurring.group_id == group_id:
                db.session.delete(recurring)
                db.session.commit()
                flash("Recurring expense deleted.", "info")

        elif action == "create_expense":
            recurring_id = request.form.get("recurring_id", type=int)
            recurring = RecurringExpense.query.get_or_404(recurring_id)
            if recurring.group_id != group_id:
                flash("Recurring expense not found.", "error")
                return redirect(url_for("group", group_id=group_id))

            expense = Expense(
                group_id=group_id,
                payer_id=recurring.payer_id,
                description=recurring.description,
                amount=recurring.amount,
                category_id=recurring.category_id,
                tags=recurring.tags,
            )
            db.session.add(expense)
            db.session.flush()

            for member in members:
                split = ExpenseSplit(expense_id=expense.id, user_id=member.id, amount_owed=round(recurring.amount / len(members), 2))
                db.session.add(split)

            recurring.last_created = datetime.utcnow()
            db.session.commit()
            flash("Expense created from recurring!", "success")
            return redirect(url_for("group", group_id=group_id))

        return redirect(url_for("manage_recurring", group_id=group_id))

    recurring = RecurringExpense.query.filter_by(group_id=group_id).order_by(RecurringExpense.created_at.desc()).all()
    return render_template("recurring.html", group=group_obj, members=members, recurring=recurring, categories=group_obj.categories)


@app.route("/group/<int:group_id>/settle", methods=["GET", "POST"])
@login_required
def settle_up(group_id):
    group_obj = Group.query.get_or_404(group_id)

    membership = GroupMember.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    if not membership:
        flash("You are not a member of this group.", "error")
        return redirect(url_for("dashboard"))

    members = [m.user for m in group_obj.members]
    balances = calculate_balances(group_id)

    if request.method == "POST":
        payer_id = request.form.get("payer_id", type=int)
        payee_id = request.form.get("payee_id", type=int)
        amount = request.form.get("amount", type=float)

        errors = []

        if not payer_id or not payee_id:
            errors.append("Please select both payer and payee.")
        if payer_id == payee_id:
            errors.append("Payer and payee cannot be the same.")
        if not amount or amount <= 0:
            errors.append("Please enter a valid amount.")

        if errors:
            for error in errors:
                flash(error, "error")
        else:
            settlement = Settlement(group_id=group_id, payer_id=payer_id, payee_id=payee_id, amount=amount)
            db.session.add(settlement)
            db.session.commit()
            flash("Settlement recorded!", "success")
            return redirect(url_for("group", group_id=group_id))

    return render_template("settle_up.html", group=group_obj, members=members, balances=balances)


@app.route("/api/group/<int:group_id>/simplify")
@login_required
def api_simplify(group_id):
    group_obj = Group.query.get_or_404(group_id)

    membership = GroupMember.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    if not membership:
        return jsonify({"error": "Not a member"}), 403

    members = [m.user for m in group_obj.members]
    balances = calculate_balances(group_id)
    simplified = simplify_debts(balances, members)

    result = []
    for t in simplified:
        from_user = User.query.get(t["from"])
        to_user = User.query.get(t["to"])
        result.append(
            {
                "from": {"id": t["from"], "username": from_user.username},
                "to": {"id": t["to"], "username": to_user.username},
                "amount": t["amount"],
            }
        )

    return jsonify(result)


@app.route("/group/<int:group_id>/export")
@login_required
def export_group(group_id):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from io import BytesIO

    group_obj = Group.query.get_or_404(group_id)

    membership = GroupMember.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    if not membership:
        flash("You are not a member of this group.", "error")
        return redirect(url_for("dashboard"))

    expenses = Expense.query.filter_by(group_id=group_id).order_by(Expense.expense_date.desc()).all()
    members = [m.user for m in group_obj.members]
    balances = calculate_balances(group_id)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph(f"Expense Report: {group_obj.name}", styles["Title"]))
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]))
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph("Expenses", styles["Heading2"]))
    data = [["Date", "Description", "Payer", "Amount"]]
    for exp in expenses:
        data.append(
            [
                exp.expense_date.strftime("%Y-%m-%d") if exp.expense_date else "-",
                exp.description[:30] + "..." if len(exp.description) > 30 else exp.description,
                exp.payer.username,
                f"₹{exp.amount:.2f}",
            ]
        )
    data.append(["", "", "Total:", f"₹{sum(e.amount for e in expenses):.2f}"])

    table = Table(data, colWidths=[1.2 * inch, 2.5 * inch, 1.2 * inch, 1 * inch])
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.grey), ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke), ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, 0), 12), ("BOTTOMPADDING", (0, 0), (-1, 0), 12), ("BACKGROUND", (0, -1), (-1, -1), colors.beige), ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"), ("GRID", (0, 0), (-1, -2), 1, colors.black)]))
    elements.append(table)
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph("Balances", styles["Heading2"]))
    bal_data = [["Member", "Balance"]]
    for member in members:
        bal = balances.get(member.id, 0)
        bal_data.append([member.username, f"₹{bal:.2f}"])

    bal_table = Table(bal_data, colWidths=[3 * inch, 1.5 * inch])
    bal_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.grey), ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke), ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("GRID", (0, 0), (-1, -1), 1, colors.black)]))
    elements.append(bal_table)

    doc.build(elements)
    buffer.seek(0)

    return buffer.read(), 200, {"Content-Type": "application/pdf", "Content-Disposition": f"attachment; filename={group_obj.name.replace(' ', '_')}_report.pdf"}


@app.route("/group/<int:group_id>/summary")
@login_required
def group_summary(group_id):
    group_obj = Group.query.get_or_404(group_id)

    membership = GroupMember.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    if not membership:
        flash("You are not a member of this group.", "error")
        return redirect(url_for("dashboard"))

    expenses = Expense.query.filter_by(group_id=group_id).all()
    members = [m.user for m in group_obj.members]
    categories = Category.query.filter_by(group_id=group_id).all()
    balances = calculate_balances(group_id)

    total_spent = sum(e.amount for e in expenses)

    category_breakdown = {}
    for cat in categories:
        cat_total = sum(e.amount for e in expenses if e.category_id == cat.id)
        if cat_total > 0:
            category_breakdown[cat.id] = {"name": cat.name, "color": cat.color, "total": cat_total, "percentage": (cat_total / total_spent * 100) if total_spent > 0 else 0}

    person_breakdown = []
    for member in members:
        paid = sum(e.amount for e in expenses if e.payer_id == member.id)
        owed = sum(e.amount for e in expenses for split in e.splits if split.user_id == member.id)
        person_breakdown.append({"user": member, "paid": paid, "owed": owed, "balance": balances.get(member.id, 0)})

    monthly_data = {}
    for exp in expenses:
        month_key = exp.expense_date.strftime("%Y-%m") if exp.expense_date else exp.created_at.strftime("%Y-%m")
        if month_key not in monthly_data:
            monthly_data[month_key] = 0
        monthly_data[month_key] += exp.amount

    return render_template(
        "summary.html",
        group=group_obj,
        total_spent=total_spent,
        category_breakdown=category_breakdown,
        person_breakdown=person_breakdown,
        monthly_data=monthly_data,
        expense_count=len(expenses),
    )


@app.route("/group/<int:group_id>/budget", methods=["GET", "POST"])
@login_required
def manage_budget(group_id):
    group_obj = Group.query.get_or_404(group_id)

    membership = GroupMember.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    if not membership:
        flash("You are not a member of this group.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        action = request.form.get("action")
        if action == "set_budget":
            category_id = request.form.get("category_id", type=int)
            budget_amount = request.form.get("budget", type=float)
            if category_id and budget_amount:
                cat = Category.query.get(category_id)
                if cat:
                    cat.budget_limit = budget_amount
                    db.session.commit()
                    flash(f"Budget set for {cat.name}!", "success")
        elif action == "clear_budget":
            category_id = request.form.get("category_id", type=int)
            if category_id:
                cat = Category.query.get(category_id)
                if cat:
                    cat.budget_limit = None
                    db.session.commit()
                    flash("Budget cleared.", "info")

        return redirect(url_for("manage_budget", group_id=group_id))

    categories = Category.query.filter_by(group_id=group_id).all()
    expenses = Expense.query.filter_by(group_id=group_id).all()

    category_status = []
    for cat in categories:
        spent = sum(e.amount for e in expenses if e.category_id == cat.id)
        category_status.append({"category": cat, "spent": spent, "budget": cat.budget_limit, "remaining": (cat.budget_limit - spent) if cat.budget_limit else None, "over": (spent > cat.budget_limit) if cat.budget_limit else False})

    return render_template("budget.html", group=group_obj, category_status=category_status)


@app.route("/admin/login", methods=["GET", "POST"])
@limiter.limit("3 per minute")
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            flash("Welcome, Admin!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid admin credentials.", "error")

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    flash("Admin logged out.", "info")
    return redirect(url_for("admin_login"))


@app.route("/admin")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    users = User.query.all()
    groups = Group.query.all()
    expenses = Expense.query.order_by(Expense.created_at.desc()).limit(50).all()
    settlements = Settlement.query.order_by(Settlement.created_at.desc()).limit(50).all()

    total_expenses = sum(e.amount for e in Expense.query.all())
    total_settlements = sum(s.amount for s in Settlement.query.all())

    return render_template(
        "admin_dashboard.html",
        users=users,
        groups=groups,
        expenses=expenses,
        settlements=settlements,
        total_expenses=total_expenses,
        total_settlements=total_settlements,
    )


@app.route("/admin/password-resets")
def admin_password_resets():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    pending_resets = PasswordReset.query.filter_by(status="pending").order_by(PasswordReset.requested_at.desc()).all()
    resolved_resets = (
        PasswordReset.query.filter_by(status="resolved").order_by(PasswordReset.resolved_at.desc()).limit(20).all()
    )

    return render_template(
        "admin_password_resets.html",
        pending_resets=pending_resets,
        resolved_resets=resolved_resets,
    )


@app.route("/admin/password-reset/<int:reset_id>/approve", methods=["GET", "POST"])
def admin_password_reset_approve(reset_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    reset_request = PasswordReset.query.get_or_404(reset_id)

    if reset_request.status != "pending":
        flash("This request has already been processed.", "error")
        return redirect(url_for("admin_password_resets"))

    if request.method == "POST":
        new_password = request.form.get("new_password", "").strip()

        if not new_password or len(new_password) < 4:
            flash("Password must be at least 4 characters.", "error")
            return redirect(url_for("admin_password_reset_approve", reset_id=reset_id))

        reset_request.user.set_password(new_password)
        reset_request.status = "resolved"
        reset_request.resolved_at = datetime.utcnow()
        reset_request.resolved_by_id = None
        reset_request.admin_notes = f"Temporary password set: {new_password}"
        db.session.commit()

        flash(f"Password reset for {reset_request.user.username}. Temp password: {new_password}", "success")
        return redirect(url_for("admin_password_resets"))

    return render_template(
        "admin_password_reset_form.html",
        reset_request=reset_request,
    )


@app.route("/admin/password-reset/<int:reset_id>/deny", methods=["POST"])
def admin_password_reset_deny(reset_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    reset_request = PasswordReset.query.get_or_404(reset_id)

    if reset_request.status != "pending":
        flash("This request has already been processed.", "error")
        return redirect(url_for("admin_password_resets"))

    reset_request.status = "denied"
    reset_request.resolved_at = datetime.utcnow()
    reset_request.resolved_by_id = None
    db.session.commit()

    flash(f"Password reset request denied for {reset_request.user.username}.", "info")
    return redirect(url_for("admin_password_resets"))


@app.route("/admin/user/<int:user_id>/delete", methods=["POST"])
def admin_delete_user(user_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'User "{user.username}" deleted.', "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/group/<int:group_id>/delete", methods=["POST"])
def admin_delete_group(group_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    group = Group.query.get_or_404(group_id)
    flash(f'Group "{group.name}" deleted.', "success")
    db.session.delete(group)
    db.session.commit()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/export")
def admin_export():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Type", "Group", "Payer", "Payee/Description", "Amount", "Date"])

    for expense in Expense.query.all():
        writer.writerow(
            [
                "Expense",
                expense.group.name,
                expense.payer.username,
                expense.description,
                expense.amount,
                expense.created_at.strftime("%Y-%m-%d %H:%M"),
            ]
        )

    for settlement in Settlement.query.all():
        writer.writerow(
            [
                "Settlement",
                settlement.group.name,
                settlement.payer.username,
                settlement.payee.username,
                settlement.amount,
                settlement.created_at.strftime("%Y-%m-%d %H:%M"),
            ]
        )

    output.seek(0)
    return (
        output.getvalue(),
        200,
        {"Content-Type": "text/csv", "Content-Disposition": "attachment; filename=samplesplit_export.csv"},
    )


def init_db():
    with app.app_context():
        db.create_all()


with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(debug=True, port=8080, host="0.0.0.0")
