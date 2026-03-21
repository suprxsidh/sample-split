import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db, calculate_balances, simplify_debts, limiter
from models import User, Group, GroupMember, Expense, ExpenseSplit, Category


@pytest.fixture
def test_client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SECRET_KEY"] = "test-secret-key"
    app.config["TESTING"] = True

    with app.app_context():
        db.create_all()
        limiter.reset()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture
def init_db():
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


@pytest.fixture
def setup_data(test_client, init_db):
    with app.app_context():
        user = User(username="testuser", email="test@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

        group = Group(name="Test Group", invite_code="123456", created_by_id=user.id)
        db.session.add(group)
        db.session.flush()

        db.session.add(GroupMember(user_id=user.id, group_id=group.id))
        db.session.commit()

        return {"user_id": user.id, "user_username": "testuser", "group_id": group.id}


@pytest.fixture
def logged_in_client(test_client, setup_data):
    test_client.post("/login", data={"username": "testuser", "password": "password123"})
    return test_client


class TestRegistration:
    def test_register_page_loads(self, test_client):
        response = test_client.get("/register")
        assert response.status_code == 200

    def test_register_valid_user(self, test_client):
        response = test_client.post(
            "/register",
            data={
                "username": "newuser",
                "email": "new@example.com",
                "password": "password123",
                "confirm_password": "password123",
            },
            follow_redirects=True,
        )
        assert b"Registration successful" in response.data or response.status_code == 200

    def test_register_password_mismatch(self, test_client):
        response = test_client.post(
            "/register",
            data={
                "username": "testuser2",
                "email": "test2@example.com",
                "password": "password123",
                "confirm_password": "different",
            },
            follow_redirects=True,
        )
        assert b"do not match" in response.data

    def test_register_short_username(self, test_client):
        response = test_client.post(
            "/register",
            data={
                "username": "ab",
                "email": "test3@example.com",
                "password": "password123",
                "confirm_password": "password123",
            },
            follow_redirects=True,
        )
        assert b"at least 3 characters" in response.data


class TestLogin:
    def test_login_page_loads(self, test_client):
        response = test_client.get("/login")
        assert response.status_code == 200

    def test_login_invalid_user(self, test_client, init_db):
        response = test_client.post(
            "/login", data={"username": "nonexistent", "password": "password123"}, follow_redirects=True
        )
        assert b"Invalid username or password" in response.data

    def test_login_valid_user(self, test_client, init_db):
        with app.app_context():
            user = User(username="logintest", email="login@test.com")
            user.set_password("password123")
            db.session.add(user)
            db.session.commit()

        response = test_client.post(
            "/login", data={"username": "logintest", "password": "password123"}, follow_redirects=True
        )
        assert b"Welcome back" in response.data


class TestDashboard:
    def test_dashboard_requires_login(self, test_client):
        response = test_client.get("/dashboard", follow_redirects=True)
        assert b"login" in response.data.lower()

    def test_dashboard_shows_groups(self, logged_in_client):
        response = logged_in_client.get("/dashboard")
        assert response.status_code == 200


class TestGroup:
    def test_create_group(self, logged_in_client, init_db):
        response = logged_in_client.post("/group/create", data={"name": "New Group"}, follow_redirects=True)
        assert response.status_code == 200

    def test_join_invalid_code(self, logged_in_client, init_db):
        response = logged_in_client.post("/group/join", data={"invite_code": "000000"}, follow_redirects=True)
        assert b"Invalid invite code" in response.data

    def test_view_group(self, logged_in_client, setup_data):
        response = logged_in_client.get("/dashboard")
        assert b"Test Group" in response.data


class TestExpense:
    def test_add_expense_equal_split(self, logged_in_client, setup_data, init_db):
        response = logged_in_client.post(
            f"/group/{setup_data['group_id']}/expense",
            data={
                "amount": "100",
                "description": "Dinner",
                "payer_id": str(setup_data["user_id"]),
                "members": [str(setup_data["user_id"])],
                "split_type": "equal",
            },
            follow_redirects=True,
        )
        assert b"added successfully" in response.data

    def test_add_expense_with_category(self, logged_in_client, setup_data, init_db):
        with app.app_context():
            cat = Category(group_id=setup_data["group_id"], name="Food", color="#ff0000")
            db.session.add(cat)
            db.session.commit()
            cat_id = cat.id

        response = logged_in_client.post(
            f"/group/{setup_data['group_id']}/expense",
            data={
                "amount": "50",
                "description": "Lunch",
                "payer_id": str(setup_data["user_id"]),
                "members": [str(setup_data["user_id"])],
                "split_type": "equal",
                "category_id": str(cat_id),
            },
            follow_redirects=True,
        )
        assert b"added successfully" in response.data

    def test_add_expense_with_tags(self, logged_in_client, setup_data, init_db):
        response = logged_in_client.post(
            f"/group/{setup_data['group_id']}/expense",
            data={
                "amount": "75",
                "description": "Movie",
                "payer_id": str(setup_data["user_id"]),
                "members": [str(setup_data["user_id"])],
                "split_type": "equal",
                "tags": "weekend, entertainment",
            },
            follow_redirects=True,
        )
        assert b"added successfully" in response.data

    def test_add_expense_percentage_split(self, logged_in_client, setup_data, init_db):
        response = logged_in_client.post(
            f"/group/{setup_data['group_id']}/expense",
            data={
                "amount": "100",
                "description": "Split by percentage",
                "payer_id": str(setup_data["user_id"]),
                "members": [str(setup_data["user_id"])],
                "split_type": "percentage",
                f"percentage_{setup_data['user_id']}": "100",
            },
            follow_redirects=True,
        )
        assert b"added successfully" in response.data

    def test_delete_expense(self, logged_in_client, setup_data, init_db):
        with app.app_context():
            expense = Expense(
                group_id=setup_data["group_id"],
                payer_id=setup_data["user_id"],
                description="To delete",
                amount=50,
            )
            db.session.add(expense)
            db.session.commit()
            expense_id = expense.id

        response = logged_in_client.post(
            f"/group/{setup_data['group_id']}/expense/{expense_id}/delete", follow_redirects=True
        )
        assert b"deleted" in response.data


class TestCategory:
    def test_add_category(self, logged_in_client, setup_data, init_db):
        response = logged_in_client.post(
            f"/group/{setup_data['group_id']}/category",
            data={"name": "Food", "icon": "fork", "color": "#ff0000"},
            follow_redirects=True,
        )
        assert b"created" in response.data

    def test_duplicate_category(self, logged_in_client, setup_data, init_db):
        with app.app_context():
            cat = Category(group_id=setup_data["group_id"], name="Travel", color="#ff0000")
            db.session.add(cat)
            db.session.commit()

        response = logged_in_client.post(
            f"/group/{setup_data['group_id']}/category",
            data={"name": "Travel", "icon": "fork", "color": "#00ff00"},
            follow_redirects=True,
        )
        assert b"already exists" in response.data

    def test_delete_category(self, logged_in_client, setup_data, init_db):
        with app.app_context():
            cat = Category(group_id=setup_data["group_id"], name="Shopping", color="#0000ff")
            db.session.add(cat)
            db.session.commit()
            cat_id = cat.id

        response = logged_in_client.post(
            f"/group/{setup_data['group_id']}/category/{cat_id}/delete", follow_redirects=True
        )
        assert b"deleted" in response.data

    def test_manage_categories_page(self, logged_in_client, setup_data):
        response = logged_in_client.get(f"/group/{setup_data['group_id']}/categories")
        assert response.status_code == 200


class TestSettlement:
    def test_record_settlement(self, logged_in_client, setup_data, init_db):
        with app.app_context():
            bob = User(username="bob", email="bob@test.com")
            bob.set_password("password")
            db.session.add(bob)
            db.session.commit()
            bob_id = bob.id

            db.session.add(GroupMember(user_id=bob.id, group_id=setup_data["group_id"]))
            db.session.commit()

        response = logged_in_client.post(
            f"/group/{setup_data['group_id']}/settle",
            data={
                "payer_id": str(bob_id),
                "payee_id": str(setup_data["user_id"]),
                "amount": "25",
            },
            follow_redirects=True,
        )
        assert b"recorded" in response.data


class TestBalanceCalculation:
    def test_equal_split_two_users(self, test_client, init_db):
        with app.app_context():
            user1 = User(username="alice", email="alice@test.com")
            user1.set_password("password")
            user2 = User(username="bob", email="bob@test.com")
            user2.set_password("password")
            db.session.add_all([user1, user2])
            db.session.commit()

            group = Group(name="Test Group", invite_code="111111", created_by_id=user1.id)
            db.session.add(group)
            db.session.flush()

            db.session.add(GroupMember(user_id=user1.id, group_id=group.id))
            db.session.add(GroupMember(user_id=user2.id, group_id=group.id))

            expense = Expense(group_id=group.id, payer_id=user1.id, description="Dinner", amount=100)
            db.session.add(expense)
            db.session.flush()

            db.session.add(ExpenseSplit(expense_id=expense.id, user_id=user1.id, amount_owed=50))
            db.session.add(ExpenseSplit(expense_id=expense.id, user_id=user2.id, amount_owed=50))
            db.session.commit()

            balances = calculate_balances(group.id)
            assert balances[user1.id] == 50
            assert balances[user2.id] == -50


class TestSimplifyDebts:
    def test_simplify_three_people(self, test_client):
        with app.app_context():
            alice = User(id=10, username="alice3", email="alice3@test.com")
            bob = User(id=20, username="bob3", email="bob3@test.com")
            charlie = User(id=30, username="charlie3", email="charlie3@test.com")

            balances = {10: 50, 20: -30, 30: -20}
            members = [alice, bob, charlie]

            transfers = simplify_debts(balances, members)

            assert len(transfers) >= 1
            total_transferred = sum(t["amount"] for t in transfers)
            assert abs(total_transferred - 50) < 0.01


class TestGroupEditing:
    def test_edit_group_name(self, logged_in_client, setup_data):
        response = logged_in_client.post(
            f"/group/{setup_data['group_id']}/edit",
            data={"name": "Updated Name"},
            follow_redirects=True,
        )
        assert b"renamed" in response.data

    def test_leave_group(self, logged_in_client, setup_data):
        response = logged_in_client.post(f"/group/{setup_data['group_id']}/leave", follow_redirects=True)
        assert b"left" in response.data


class TestSearch:
    def test_search_expenses(self, logged_in_client, setup_data, init_db):
        with app.app_context():
            expense = Expense(
                group_id=setup_data["group_id"],
                payer_id=setup_data["user_id"],
                description="Pizza",
                amount=50,
            )
            db.session.add(expense)
            db.session.commit()

        response = logged_in_client.get(f"/group/{setup_data['group_id']}?q=Pizza")
        assert b"Pizza" in response.data


class TestCategorySummary:
    def test_category_summary(self, logged_in_client, setup_data, init_db):
        with app.app_context():
            cat = Category(group_id=setup_data["group_id"], name="Food", color="#ff0000")
            db.session.add(cat)
            db.session.commit()

            expense = Expense(
                group_id=setup_data["group_id"],
                payer_id=setup_data["user_id"],
                description="Lunch",
                amount=100,
                category_id=cat.id,
            )
            db.session.add(expense)
            db.session.commit()

        response = logged_in_client.get(f"/group/{setup_data['group_id']}")
        assert b"Food" in response.data


class TestAdmin:
    def test_admin_login_page(self, test_client):
        response = test_client.get("/admin/login")
        assert response.status_code == 200

    def test_admin_login_invalid(self, test_client):
        response = test_client.post("/admin/login", data={"username": "wrong", "password": "wrong"})
        assert b"Invalid" in response.data

    def test_admin_login_valid(self, test_client):
        response = test_client.post("/admin/login", data={"username": "admin", "password": "password1234"})
        assert response.status_code == 302

    def test_admin_dashboard(self, test_client):
        test_client.post("/admin/login", data={"username": "admin", "password": "password1234"})
        response = test_client.get("/admin")
        assert response.status_code == 200

    def test_admin_logout(self, test_client):
        test_client.post("/admin/login", data={"username": "admin", "password": "password1234"})
        response = test_client.get("/admin/logout")
        assert response.status_code == 302


class TestAPI:
    def test_simplify_api(self, logged_in_client, setup_data, init_db):
        with app.app_context():
            bob = User(username="bob2", email="bob2@test.com")
            bob.set_password("password")
            db.session.add(bob)
            db.session.commit()

            db.session.add(GroupMember(user_id=bob.id, group_id=setup_data["group_id"]))
            db.session.commit()

            expense = Expense(
                group_id=setup_data["group_id"],
                payer_id=setup_data["user_id"],
                description="Dinner",
                amount=100,
            )
            db.session.add(expense)
            db.session.flush()

            db.session.add(ExpenseSplit(expense_id=expense.id, user_id=setup_data["user_id"], amount_owed=50))
            db.session.add(ExpenseSplit(expense_id=expense.id, user_id=bob.id, amount_owed=50))
            db.session.commit()

        response = logged_in_client.get(f"/api/group/{setup_data['group_id']}/simplify")
        assert response.status_code == 200


class TestSortAndFilter:
    def test_sort_by_amount(self, logged_in_client, setup_data, init_db):
        with app.app_context():
            expense = Expense(
                group_id=setup_data["group_id"],
                payer_id=setup_data["user_id"],
                description="Small",
                amount=10,
            )
            db.session.add(expense)
            expense2 = Expense(
                group_id=setup_data["group_id"],
                payer_id=setup_data["user_id"],
                description="Large",
                amount=100,
            )
            db.session.add(expense2)
            db.session.commit()

        response = logged_in_client.get(f"/group/{setup_data['group_id']}?sort=amount_desc")
        assert response.status_code == 200

    def test_category_filter(self, logged_in_client, setup_data, init_db):
        with app.app_context():
            cat = Category(group_id=setup_data["group_id"], name="Travel", color="#0000ff")
            db.session.add(cat)
            db.session.commit()
            cat_id = cat.id

            expense = Expense(
                group_id=setup_data["group_id"],
                payer_id=setup_data["user_id"],
                description="Trip",
                amount=50,
                category_id=cat_id,
            )
            db.session.add(expense)
            db.session.commit()

        response = logged_in_client.get(f"/group/{setup_data['group_id']}?category={cat_id}")
        assert response.status_code == 200


class TestRemoveMember:
    def test_remove_member(self, logged_in_client, setup_data, init_db):
        with app.app_context():
            bob = User(username="bob3", email="bob3@test.com")
            bob.set_password("password")
            db.session.add(bob)
            db.session.commit()
            bob_id = bob.id

            db.session.add(GroupMember(user_id=bob.id, group_id=setup_data["group_id"]))
            db.session.commit()

        response = logged_in_client.post(f"/group/{setup_data['group_id']}/remove/{bob_id}", follow_redirects=True)
        assert b"removed" in response.data


class TestComments:
    def test_add_comment(self, logged_in_client, setup_data, init_db):
        with app.app_context():
            expense = Expense(
                group_id=setup_data["group_id"],
                payer_id=setup_data["user_id"],
                description="Test expense",
                amount=50,
            )
            db.session.add(expense)
            db.session.commit()
            expense_id = expense.id

        response = logged_in_client.post(
            f"/group/{setup_data['group_id']}/expense/{expense_id}/comment",
            data={"content": "Great expense!"},
            follow_redirects=True,
        )
        assert b"added" in response.data

    def test_empty_comment(self, logged_in_client, setup_data, init_db):
        with app.app_context():
            expense = Expense(
                group_id=setup_data["group_id"],
                payer_id=setup_data["user_id"],
                description="Test expense 2",
                amount=50,
            )
            db.session.add(expense)
            db.session.commit()
            expense_id = expense.id

        response = logged_in_client.post(
            f"/group/{setup_data['group_id']}/expense/{expense_id}/comment", data={"content": ""}, follow_redirects=True
        )
        assert b"empty" in response.data


class TestRecurring:
    def test_create_recurring(self, logged_in_client, setup_data, init_db):
        response = logged_in_client.post(
            f"/group/{setup_data['group_id']}/recurring",
            data={
                "action": "create",
                "description": "Monthly Rent",
                "amount": "1000",
                "payer_id": str(setup_data["user_id"]),
                "frequency": "monthly",
            },
            follow_redirects=True,
        )
        assert b"created" in response.data

    def test_manage_recurring_page(self, logged_in_client, setup_data, init_db):
        response = logged_in_client.get(f"/group/{setup_data['group_id']}/recurring")
        assert response.status_code == 200

    def test_toggle_recurring(self, logged_in_client, setup_data, init_db):
        with app.app_context():
            from models import RecurringExpense

            recurring = RecurringExpense(
                group_id=setup_data["group_id"],
                payer_id=setup_data["user_id"],
                description="Test",
                amount=100,
            )
            db.session.add(recurring)
            db.session.commit()
            rec_id = recurring.id

        response = logged_in_client.post(
            f"/group/{setup_data['group_id']}/recurring",
            data={"action": "toggle", "recurring_id": str(rec_id)},
            follow_redirects=True,
        )
        assert response.status_code == 200

    def test_invalid_amount_recurring(self, logged_in_client, setup_data, init_db):
        response = logged_in_client.post(
            f"/group/{setup_data['group_id']}/recurring",
            data={
                "action": "create",
                "description": "Invalid",
                "amount": "-10",
                "payer_id": str(setup_data["user_id"]),
                "frequency": "monthly",
            },
            follow_redirects=True,
        )
        assert b"valid amount" in response.data


class TestReceipt:
    def test_receipt_upload_page(self, logged_in_client, setup_data, init_db):
        with app.app_context():
            expense = Expense(
                group_id=setup_data["group_id"],
                payer_id=setup_data["user_id"],
                description="Receipt test",
                amount=50,
            )
            db.session.add(expense)
            db.session.commit()

        response = logged_in_client.get(f"/group/{setup_data['group_id']}")
        assert b"receipt" in response.data.lower() or b"upload" in response.data.lower()


class TestRecurringActions:
    def test_create_expense_from_recurring(self, logged_in_client, setup_data, init_db):
        with app.app_context():
            from models import RecurringExpense

            recurring = RecurringExpense(
                group_id=setup_data["group_id"],
                payer_id=setup_data["user_id"],
                description="Rent",
                amount=500,
            )
            db.session.add(recurring)
            db.session.commit()
            rec_id = recurring.id

            response = logged_in_client.post(
                f"/group/{setup_data['group_id']}/recurring",
                data={"action": "create_expense", "recurring_id": str(rec_id)},
                follow_redirects=True,
            )
            assert b"created from recurring" in response.data


class TestSummary:
    def test_group_summary_page(self, logged_in_client, setup_data, init_db):
        response = logged_in_client.get(f"/group/{setup_data['group_id']}/summary")
        assert response.status_code == 200

    def test_export_pdf(self, logged_in_client, setup_data, init_db):
        with app.app_context():
            expense = Expense(
                group_id=setup_data["group_id"],
                payer_id=setup_data["user_id"],
                description="Test",
                amount=100,
            )
            db.session.add(expense)
            db.session.commit()

        response = logged_in_client.get(f"/group/{setup_data['group_id']}/export")
        assert response.status_code == 200
        assert b"%PDF" in response.data


class TestBudget:
    def test_budget_page(self, logged_in_client, setup_data, init_db):
        response = logged_in_client.get(f"/group/{setup_data['group_id']}/budget")
        assert response.status_code == 200

    def test_set_budget(self, logged_in_client, setup_data, init_db):
        with app.app_context():
            from models import Category

            cat = Category(group_id=setup_data["group_id"], name="Food", color="#ff0000")
            db.session.add(cat)
            db.session.commit()
            cat_id = cat.id

        response = logged_in_client.post(
            f"/group/{setup_data['group_id']}/budget",
            data={"action": "set_budget", "category_id": str(cat_id), "budget": "500"},
            follow_redirects=True,
        )
        assert response.status_code == 200


class TestExpenseExactSplit:
    def test_add_expense_exact_split(self, logged_in_client, setup_data, init_db):
        response = logged_in_client.post(
            f"/group/{setup_data['group_id']}/expense",
            data={
                "amount": "100",
                "description": "Exact split dinner",
                "payer_id": str(setup_data["user_id"]),
                "members": [str(setup_data["user_id"])],
                "split_type": "exact",
                f"amount_{setup_data['user_id']}": "100",
            },
            follow_redirects=True,
        )
        assert b"added successfully" in response.data

    def test_add_expense_exact_split_wrong_total(self, logged_in_client, setup_data, init_db):
        with app.app_context():
            bob = User(username="exact_split_bob", email="exactbob@test.com")
            bob.set_password("password")
            db.session.add(bob)
            db.session.commit()
            bob_id = bob.id
            db.session.add(GroupMember(user_id=bob.id, group_id=setup_data["group_id"]))
            db.session.commit()

        response = logged_in_client.post(
            f"/group/{setup_data['group_id']}/expense",
            data={
                "amount": "100",
                "description": "Wrong total",
                "payer_id": str(setup_data["user_id"]),
                "members": [str(setup_data["user_id"]), str(bob_id)],
                "split_type": "exact",
                f"amount_{setup_data['user_id']}": "30",
                f"amount_{bob_id}": "30",
            },
            follow_redirects=True,
        )
        assert b"100.00" in response.data


class TestExpensePercentageValidation:
    def test_percentage_wrong_total(self, logged_in_client, setup_data, init_db):
        with app.app_context():
            bob = User(username="pct_bob", email="pctbob@test.com")
            bob.set_password("password")
            db.session.add(bob)
            db.session.commit()
            bob_id = bob.id
            db.session.add(GroupMember(user_id=bob.id, group_id=setup_data["group_id"]))
            db.session.commit()

        response = logged_in_client.post(
            f"/group/{setup_data['group_id']}/expense",
            data={
                "amount": "100",
                "description": "Percentage wrong",
                "payer_id": str(setup_data["user_id"]),
                "members": [str(setup_data["user_id"]), str(bob_id)],
                "split_type": "percentage",
                f"percentage_{setup_data['user_id']}": "30",
                f"percentage_{bob_id}": "30",
            },
            follow_redirects=True,
        )
        assert b"100%" in response.data


class TestLeaveGroup:
    def test_leave_group_last_member(self, logged_in_client, setup_data):
        response = logged_in_client.post(
            f"/group/{setup_data['group_id']}/leave",
            follow_redirects=True,
        )
        assert b"left" in response.data


class TestRecurringDelete:
    def test_delete_recurring(self, logged_in_client, setup_data, init_db):
        with app.app_context():
            from models import RecurringExpense

            recurring = RecurringExpense(
                group_id=setup_data["group_id"],
                payer_id=setup_data["user_id"],
                description="To delete",
                amount=100,
            )
            db.session.add(recurring)
            db.session.commit()
            rec_id = recurring.id

        response = logged_in_client.post(
            f"/group/{setup_data['group_id']}/recurring",
            data={"action": "delete", "recurring_id": str(rec_id)},
            follow_redirects=True,
        )
        assert b"deleted" in response.data


class TestBudgetEdgeCases:
    def test_budget_over_limit(self, logged_in_client, setup_data, init_db):
        with app.app_context():
            from models import Category, Expense

            cat = Category(group_id=setup_data["group_id"], name="Food", color="#ff0000", budget_limit=50)
            db.session.add(cat)
            db.session.commit()
            cat_id = cat.id

            expense = Expense(
                group_id=setup_data["group_id"],
                payer_id=setup_data["user_id"],
                description="Over budget",
                amount=75,
                category_id=cat_id,
            )
            db.session.add(expense)
            db.session.commit()

        response = logged_in_client.get(f"/group/{setup_data['group_id']}/budget")
        assert response.status_code == 200

    def test_budget_clear(self, logged_in_client, setup_data, init_db):
        with app.app_context():
            from models import Category

            cat = Category(group_id=setup_data["group_id"], name="Travel", color="#0000ff", budget_limit=200)
            db.session.add(cat)
            db.session.commit()
            cat_id = cat.id

        response = logged_in_client.post(
            f"/group/{setup_data['group_id']}/budget",
            data={"action": "clear_budget", "category_id": str(cat_id)},
            follow_redirects=True,
        )
        assert b"cleared" in response.data


class TestForgotPassword:
    def test_forgot_password_page(self, test_client):
        response = test_client.get("/forgot-password")
        assert response.status_code == 200

    def test_forgot_password_submit(self, test_client, init_db):
        with app.app_context():
            user = User(username="forgotpw_user", email="forgotpw@test.com")
            user.set_password("password")
            db.session.add(user)
            db.session.commit()

        response = test_client.post(
            "/forgot-password",
            data={"identifier": "forgotpw_user"},
            follow_redirects=True,
        )
        assert b"reset request submitted" in response.data or b"contact an administrator" in response.data

    def test_forgot_password_nonexistent(self, test_client, init_db):
        response = test_client.post(
            "/forgot-password",
            data={"identifier": "nonexistentuser123"},
            follow_redirects=True,
        )
        assert b"if an account exists" in response.data or response.status_code == 200


class TestExpenseDate:
    def test_add_expense_with_date(self, logged_in_client, setup_data, init_db):
        response = logged_in_client.post(
            f"/group/{setup_data['group_id']}/expense",
            data={
                "amount": "50",
                "description": "Yesterday's dinner",
                "payer_id": str(setup_data["user_id"]),
                "members": [str(setup_data["user_id"])],
                "split_type": "equal",
                "expense_date": "2026-01-15",
            },
            follow_redirects=True,
        )
        assert b"added successfully" in response.data

    def test_add_expense_invalid_date(self, logged_in_client, setup_data, init_db):
        response = logged_in_client.post(
            f"/group/{setup_data['group_id']}/expense",
            data={
                "amount": "50",
                "description": "Bad date",
                "payer_id": str(setup_data["user_id"]),
                "members": [str(setup_data["user_id"])],
                "split_type": "equal",
                "expense_date": "not-a-date",
            },
            follow_redirects=True,
        )
        assert b"Invalid date" in response.data


class TestSettlementFlow:
    def test_settlement_two_users(self, logged_in_client, setup_data, init_db):
        with app.app_context():
            bob = User(username="settle_bob", email="settle_bob@test.com")
            bob.set_password("password")
            db.session.add(bob)
            db.session.commit()
            bob_id = bob.id
            db.session.add(GroupMember(user_id=bob.id, group_id=setup_data["group_id"]))
            db.session.commit()

        logged_in_client.post(
            f"/group/{setup_data['group_id']}/expense",
            data={
                "amount": "100",
                "description": "Dinner",
                "payer_id": str(setup_data["user_id"]),
                "members": [str(setup_data["user_id"]), str(bob_id)],
                "split_type": "equal",
            },
        )

        response = logged_in_client.post(
            f"/group/{setup_data['group_id']}/settle",
            data={
                "payer_id": str(bob_id),
                "payee_id": str(setup_data["user_id"]),
                "amount": "50",
            },
            follow_redirects=True,
        )
        assert b"recorded" in response.data


class TestSimplifyDebtsEdgeCases:
    def test_simplify_all_balances_zero(self, test_client):
        with app.app_context():
            alice = User(id=100, username="alice100", email="alice100@test.com")
            bob = User(id=200, username="bob200", email="bob200@test.com")
            balances = {100: 0, 200: 0}
            members = [alice, bob]
            transfers = simplify_debts(balances, members)
            assert len(transfers) == 0

    def test_simplify_exact_two_person(self, test_client):
        with app.app_context():
            alice = User(id=300, username="alice300", email="alice300@test.com")
            bob = User(id=400, username="bob400", email="bob400@test.com")
            balances = {300: 100, 400: -100}
            members = [alice, bob]
            transfers = simplify_debts(balances, members)
            assert len(transfers) == 1
            assert transfers[0]["amount"] == 100
            assert transfers[0]["from"] == 400
            assert transfers[0]["to"] == 300


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
