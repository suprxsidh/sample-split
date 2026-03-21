import os

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models import db, User, Group, GroupMember, Expense, ExpenseSplit, Settlement
from datetime import datetime
import csv
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///samplesplit.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED'] = True

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password123'

db.init_app(app)
csrf = CSRFProtect(app)

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def calculate_balances(group_id):
    group = Group.query.get_or_404(group_id)
    members = [m.user for m in group.members]
    member_ids = {m.id for m in members}
    
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
            creditors.append({'user_id': user_id, 'amount': balance})
        elif balance < -0.01:
            debtors.append({'user_id': user_id, 'amount': -balance})
    
    creditors.sort(key=lambda x: x['amount'], reverse=True)
    debtors.sort(key=lambda x: x['amount'], reverse=True)
    
    transfers = []
    i, j = 0, 0
    
    while i < len(creditors) and j < len(debtors):
        creditor = creditors[i]
        debtor = debtors[j]
        
        amount = min(creditor['amount'], debtor['amount'])
        
        if amount > 0.01:
            transfers.append({
                'from': debtor['user_id'],
                'to': creditor['user_id'],
                'amount': round(amount, 2)
            })
        
        creditor['amount'] -= amount
        debtor['amount'] -= amount
        
        if creditor['amount'] < 0.01:
            i += 1
        if debtor['amount'] < 0.01:
            j += 1
    
    return transfers

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        errors = []
        
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if not email or '@' not in email:
            errors.append('Please enter a valid email address.')
        if not password or len(password) < 4:
            errors.append('Password must be at least 4 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if User.query.filter_by(username=username).first():
            errors.append('Username already taken.')
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Welcome back!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    groups = current_user.get_groups()
    group_balances = {}
    
    for group in groups:
        balances = calculate_balances(group.id)
        user_balance = balances.get(current_user.id, 0)
        group_balances[group.id] = round(user_balance, 2)
    
    return render_template('dashboard.html', groups=groups, group_balances=group_balances)

@app.route('/group/create', methods=['GET', 'POST'])
@login_required
def create_group():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        
        if not name:
            flash('Group name is required.', 'error')
            return render_template('create_group.html')
        
        invite_code = Group.generate_invite_code()
        group = Group(name=name, invite_code=invite_code, created_by_id=current_user.id)
        db.session.add(group)
        db.session.flush()
        
        member = GroupMember(user_id=current_user.id, group_id=group.id)
        db.session.add(member)
        db.session.commit()
        
        flash(f'Group "{name}" created! Invite code: {invite_code}', 'success')
        return redirect(url_for('group', group_id=group.id))
    
    return render_template('create_group.html')

@app.route('/group/join', methods=['GET', 'POST'])
@login_required
def join_group():
    if request.method == 'POST':
        invite_code = request.form.get('invite_code', '').strip()
        
        if not invite_code or len(invite_code) != 6:
            flash('Please enter a valid 6-digit invite code.', 'error')
            return render_template('join_group.html')
        
        group = Group.query.filter_by(invite_code=invite_code).first()
        
        if not group:
            flash('Invalid invite code. Please check and try again.', 'error')
            return render_template('join_group.html')
        
        existing = GroupMember.query.filter_by(user_id=current_user.id, group_id=group.id).first()
        if existing:
            flash('You are already a member of this group.', 'info')
            return redirect(url_for('group', group_id=group.id))
        
        member = GroupMember(user_id=current_user.id, group_id=group.id)
        db.session.add(member)
        db.session.commit()
        
        flash(f'Successfully joined "{group.name}"!', 'success')
        return redirect(url_for('group', group_id=group.id))
    
    return render_template('join_group.html')

@app.route('/group/<int:group_id>')
@app.route('/group/<int:group_id>')
@login_required
def group(group_id):
    group_obj = Group.query.get_or_404(group_id)
    
    membership = GroupMember.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    if not membership:
        flash('You are not a member of this group.', 'error')
        return redirect(url_for('dashboard'))
    
    members = [m.user for m in group_obj.members]
    balances = calculate_balances(group_id)
    simplified = simplify_debts(balances, members)
    
    member_balances = {}
    for user in members:
        member_balances[user.id] = {
            'user': user,
            'balance': round(balances.get(user.id, 0), 2)
        }
    
    search_query = request.args.get('q', '').strip()
    
    expenses = Expense.query.filter_by(group_id=group_id)
    if search_query:
        expenses = expenses.filter(Expense.description.ilike(f'%{search_query}%'))
    expenses = expenses.order_by(Expense.created_at.desc()).all()
    
    settlements = Settlement.query.filter_by(group_id=group_id).order_by(Settlement.created_at.desc()).limit(10).all()
    
    all_transactions = []
    for expense in expenses:
        all_transactions.append({
            'type': 'expense',
            'data': expense,
            'created_at': expense.created_at
        })
    for settlement in settlements:
        all_transactions.append({
            'type': 'settlement',
            'data': settlement,
            'created_at': settlement.created_at
        })
    all_transactions.sort(key=lambda x: x['created_at'], reverse=True)
    
    user_balance = balances.get(current_user.id, 0)
    
    return render_template('group.html', 
                         group=group_obj, 
                         members=members,
                         member_balances=member_balances,
                         simplified=simplified,
                         transactions=all_transactions,
                         user_balance=round(user_balance, 2),
                         search_query=search_query)

@app.route('/group/<int:group_id>/edit', methods=['POST'])
@login_required
def edit_group(group_id):
    group_obj = Group.query.get_or_404(group_id)
    
    membership = GroupMember.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    if not membership:
        flash('You are not a member of this group.', 'error')
        return redirect(url_for('dashboard'))
    
    new_name = request.form.get('name', '').strip()
    if new_name:
        group_obj.name = new_name
        db.session.commit()
        flash(f'Group renamed to "{new_name}"', 'success')
    
    return redirect(url_for('group', group_id=group_id))

@app.route('/group/<int:group_id>/leave', methods=['POST'])
@login_required
def leave_group(group_id):
    group_obj = Group.query.get_or_404(group_id)
    
    membership = GroupMember.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    if not membership:
        flash('You are not a member of this group.', 'error')
        return redirect(url_for('dashboard'))
    
    db.session.delete(membership)
    db.session.commit()
    flash(f'You left "{group_obj.name}"', 'info')
    return redirect(url_for('dashboard'))

@app.route('/group/<int:group_id>/expense', methods=['GET', 'POST'])
@login_required
def add_expense(group_id):
    group_obj = Group.query.get_or_404(group_id)
    
    membership = GroupMember.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    if not membership:
        flash('You are not a member of this group.', 'error')
        return redirect(url_for('dashboard'))
    
    members = [m.user for m in group_obj.members]
    
    if request.method == 'POST':
        amount = request.form.get('amount', type=float)
        description = request.form.get('description', '').strip()
        payer_id = request.form.get('payer_id', type=int)
        selected_members = request.form.getlist('members')
        expense_date_str = request.form.get('expense_date', '')
        split_type = request.form.get('split_type', 'equal')
        
        errors = []
        
        if not amount or amount <= 0:
            errors.append('Please enter a valid amount.')
        if not payer_id:
            errors.append('Please select who paid.')
        if not selected_members:
            errors.append('Please select at least one person to split with.')
        if payer_id and int(payer_id) not in [m.id for m in members]:
            errors.append('Invalid payer selected.')
        for mid in selected_members:
            if int(mid) not in [m.id for m in members]:
                errors.append('Invalid member selected.')
        
        expense_date = datetime.utcnow().date()
        if expense_date_str:
            try:
                expense_date = datetime.strptime(expense_date_str, '%Y-%m-%d').date()
            except:
                errors.append('Invalid date format.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
        else:
            splits = []
            
            if split_type == 'equal':
                split_amount = amount / len(selected_members)
                for member_id in selected_members:
                    splits.append((int(member_id), round(split_amount, 2)))
            
            elif split_type == 'percentage':
                for member_id in selected_members:
                    pct_key = f'percentage_{member_id}'
                    pct = request.form.get(pct_key, type=float, default=0)
                    split_amount = (pct / 100) * amount
                    splits.append((int(member_id), round(split_amount, 2)))
                
                total_pct = sum(float(request.form.get(f'percentage_{mid}', 0)) for mid in selected_members)
                if abs(total_pct - 100) > 0.1:
                    flash(f'Percentages must total 100% (currently {total_pct:.1f}%)', 'error')
                    return render_template('add_expense.html', group=group_obj, members=members)
            
            elif split_type == 'exact':
                remaining = amount
                last_member = None
                
                for member_id in selected_members:
                    amt_key = f'amount_{member_id}'
                    split_amount = request.form.get(amt_key, type=float, default=0)
                    splits.append((int(member_id), split_amount))
                    remaining -= split_amount
                    last_member = member_id
                
                if abs(remaining) > 0.01:
                    if last_member and abs(remaining) < amount:
                        splits = [(mid, float(request.form.get(f'amount_{mid}', 0)) if mid != last_member else round(float(request.form.get(f'amount_{mid}', 0)) + remaining, 2)) for mid in selected_members]
                    else:
                        flash(f'Amounts must total ₹{amount:.2f}', 'error')
                        return render_template('add_expense.html', group=group_obj, members=members)
            
            expense = Expense(
                group_id=group_id,
                payer_id=payer_id,
                description=description or 'Expense',
                amount=amount,
                expense_date=expense_date
            )
            db.session.add(expense)
            db.session.flush()
            
            for user_id, amount_owed in splits:
                split = ExpenseSplit(
                    expense_id=expense.id,
                    user_id=user_id,
                    amount_owed=amount_owed
                )
                db.session.add(split)
            
            db.session.commit()
            flash('Expense added successfully!', 'success')
            return redirect(url_for('group', group_id=group_id))
    
    return render_template('add_expense.html', group=group_obj, members=members)

@app.route('/group/<int:group_id>/expense/<int:expense_id>/delete', methods=['POST'])
@login_required
def delete_expense(group_id, expense_id):
    expense = Expense.query.get_or_404(expense_id)
    
    if expense.payer_id != current_user.id:
        flash('Only the person who created this expense can delete it.', 'error')
        return redirect(url_for('group', group_id=group_id))
    
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted.', 'success')
    return redirect(url_for('group', group_id=group_id))

@app.route('/group/<int:group_id>/settle', methods=['GET', 'POST'])
@login_required
def settle_up(group_id):
    group_obj = Group.query.get_or_404(group_id)
    
    membership = GroupMember.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    if not membership:
        flash('You are not a member of this group.', 'error')
        return redirect(url_for('dashboard'))
    
    members = [m.user for m in group_obj.members]
    balances = calculate_balances(group_id)
    
    if request.method == 'POST':
        payer_id = request.form.get('payer_id', type=int)
        payee_id = request.form.get('payee_id', type=int)
        amount = request.form.get('amount', type=float)
        
        errors = []
        
        if not payer_id or not payee_id:
            errors.append('Please select both payer and payee.')
        if payer_id == payee_id:
            errors.append('Payer and payee cannot be the same.')
        if not amount or amount <= 0:
            errors.append('Please enter a valid amount.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
        else:
            settlement = Settlement(
                group_id=group_id,
                payer_id=payer_id,
                payee_id=payee_id,
                amount=amount
            )
            db.session.add(settlement)
            db.session.commit()
            flash('Settlement recorded!', 'success')
            return redirect(url_for('group', group_id=group_id))
    
    return render_template('settle_up.html', group=group_obj, members=members, balances=balances)

@app.route('/api/group/<int:group_id>/simplify')
@login_required
def api_simplify(group_id):
    group_obj = Group.query.get_or_404(group_id)
    
    membership = GroupMember.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    if not membership:
        return jsonify({'error': 'Not a member'}), 403
    
    members = [m.user for m in group_obj.members]
    balances = calculate_balances(group_id)
    simplified = simplify_debts(balances, members)
    
    result = []
    for t in simplified:
        from_user = User.query.get(t['from'])
        to_user = User.query.get(t['to'])
        result.append({
            'from': {'id': t['from'], 'username': from_user.username},
            'to': {'id': t['to'], 'username': to_user.username},
            'amount': t['amount']
        })
    
    return jsonify(result)

@app.route('/admin/login', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Welcome, Admin!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials.', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Admin logged out.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    users = User.query.all()
    groups = Group.query.all()
    expenses = Expense.query.order_by(Expense.created_at.desc()).limit(50).all()
    settlements = Settlement.query.order_by(Settlement.created_at.desc()).limit(50).all()
    
    total_expenses = sum(e.amount for e in Expense.query.all())
    total_settlements = sum(s.amount for s in Settlement.query.all())
    
    return render_template('admin_dashboard.html', 
                         users=users,
                         groups=groups,
                         expenses=expenses,
                         settlements=settlements,
                         total_expenses=total_expenses,
                         total_settlements=total_settlements)

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
def admin_delete_user(user_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'User "{user.username}" deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/group/<int:group_id>/delete', methods=['POST'])
def admin_delete_group(group_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    group = Group.query.get_or_404(group_id)
    flash(f'Group "{group.name}" deleted.', 'success')
    db.session.delete(group)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/export')
def admin_export():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['Type', 'Group', 'Payer', 'Payee/Description', 'Amount', 'Date'])
    
    for expense in Expense.query.all():
        writer.writerow([
            'Expense',
            expense.group.name,
            expense.payer.username,
            expense.description,
            expense.amount,
            expense.created_at.strftime('%Y-%m-%d %H:%M')
        ])
    
    for settlement in Settlement.query.all():
        writer.writerow([
            'Settlement',
            settlement.group.name,
            settlement.payer.username,
            settlement.payee.username,
            settlement.amount,
            settlement.created_at.strftime('%Y-%m-%d %H:%M')
        ])
    
    output.seek(0)
    return output.getvalue(), 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename=samplesplit_export.csv'
    }

def init_db():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=8080, host='0.0.0.0')
