from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
import random
import string

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    memberships = db.relationship("GroupMember", back_populates="user", cascade="all, delete-orphan")
    expenses_paid = db.relationship("Expense", back_populates="payer", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_groups(self):
        return [m.group for m in self.memberships]


class Group(db.Model):
    __tablename__ = "groups"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    invite_code = db.Column(db.String(6), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    allow_on_behalf_expenses = db.Column(db.Boolean, default=False, nullable=False)

    created_by = db.relationship("User", foreign_keys=[created_by_id])
    members = db.relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    expenses = db.relationship("Expense", back_populates="group", cascade="all, delete-orphan")
    settlements = db.relationship("Settlement", back_populates="group", cascade="all, delete-orphan")
    categories = db.relationship("Category", back_populates="group", cascade="all, delete-orphan")
    recurring_expenses = db.relationship("RecurringExpense", back_populates="group", cascade="all, delete-orphan")

    @staticmethod
    def generate_invite_code():
        while True:
            code = "".join(random.choices(string.digits, k=6))
            if not Group.query.filter_by(invite_code=code).first():
                return code


class GroupMember(db.Model):
    __tablename__ = "group_members"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    joined_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    user = db.relationship("User", back_populates="memberships")
    group = db.relationship("Group", back_populates="members")

    __table_args__ = (db.UniqueConstraint("user_id", "group_id", name="unique_member_per_group"),)


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    icon = db.Column(db.String(20), default="tag")
    color = db.Column(db.String(7), default="#6b7280")
    budget_limit = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    group = db.relationship("Group", back_populates="categories")
    expenses = db.relationship("Expense", back_populates="category")

    __table_args__ = (db.UniqueConstraint("group_id", "name", name="unique_category_per_group"),)


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    payer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    description = db.Column(db.String(200), default="")
    amount = db.Column(db.Float, nullable=False)
    expense_date = db.Column(db.Date, default=lambda: datetime.now(timezone.utc).date())
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    tags = db.Column(db.String(200), default="")

    group = db.relationship("Group", back_populates="expenses")
    payer = db.relationship("User", back_populates="expenses_paid")
    splits = db.relationship("ExpenseSplit", back_populates="expense", cascade="all, delete-orphan")
    category = db.relationship("Category", back_populates="expenses")
    comments = db.relationship("Comment", back_populates="expense", cascade="all, delete-orphan")
    receipt_url = db.Column(db.String(500), nullable=True)


class RecurringExpense(db.Model):
    __tablename__ = "recurring_expenses"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    payer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    description = db.Column(db.String(200), default="")
    amount = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    tags = db.Column(db.String(200), default="")
    frequency = db.Column(db.String(20), default="monthly")
    last_created = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_active = db.Column(db.Boolean, default=True)

    group = db.relationship("Group")
    payer = db.relationship("User")


class ExpenseSplit(db.Model):
    __tablename__ = "expense_splits"

    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey("expenses.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount_owed = db.Column(db.Float, nullable=False)

    expense = db.relationship("Expense", back_populates="splits")
    user = db.relationship("User")


class Settlement(db.Model):
    __tablename__ = "settlements"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    payer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    payee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    group = db.relationship("Group", back_populates="settlements")
    payer = db.relationship("User", foreign_keys=[payer_id])
    payee = db.relationship("User", foreign_keys=[payee_id])


class PasswordReset(db.Model):
    __tablename__ = "password_resets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    requested_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    status = db.Column(db.String(20), default="pending")
    admin_notes = db.Column(db.Text, default="")
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolved_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    user = db.relationship("User", foreign_keys=[user_id])
    resolved_by = db.relationship("User", foreign_keys=[resolved_by_id])


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey("expenses.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    expense = db.relationship("Expense", back_populates="comments")
    user = db.relationship("User")
