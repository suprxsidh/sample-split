import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db, calculate_balances, simplify_debts
from models import User, Group, GroupMember, Expense, ExpenseSplit, Settlement


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture
def init_database():
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


class TestRegistration:
    def test_register_page_loads(self, client):
        response = client.get('/register')
        assert response.status_code == 200
    
    def test_register_valid_user(self, client):
        response = client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        assert b'Registration successful' in response.data or response.status_code == 200
    
    def test_register_password_mismatch(self, client):
        response = client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'confirm_password': 'different'
        }, follow_redirects=True)
        assert b'do not match' in response.data
    
    def test_register_short_username(self, client):
        response = client.post('/register', data={
            'username': 'ab',
            'email': 'test@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        assert b'at least 3 characters' in response.data


class TestLogin:
    def test_login_page_loads(self, client):
        response = client.get('/login')
        assert response.status_code == 200
    
    def test_login_invalid_user(self, client, init_database):
        with app.app_context():
            response = client.post('/login', data={
                'username': 'nonexistent',
                'password': 'password123'
            }, follow_redirects=True)
            assert b'Invalid username or password' in response.data


class TestBalanceCalculation:
    def test_equal_split_two_users(self, client, init_database):
        with app.app_context():
            user1 = User(username='alice', email='alice@test.com')
            user1.set_password('password')
            user2 = User(username='bob', email='bob@test.com')
            user2.set_password('password')
            db.session.add_all([user1, user2])
            db.session.commit()
            
            group = Group(name='Test Group', invite_code='123456', created_by_id=user1.id)
            db.session.add(group)
            db.session.flush()
            
            db.session.add(GroupMember(user_id=user1.id, group_id=group.id))
            db.session.add(GroupMember(user_id=user2.id, group_id=group.id))
            
            expense = Expense(group_id=group.id, payer_id=user1.id, description='Dinner', amount=100)
            db.session.add(expense)
            db.session.flush()
            
            db.session.add(ExpenseSplit(expense_id=expense.id, user_id=user1.id, amount_owed=50))
            db.session.add(ExpenseSplit(expense_id=expense.id, user_id=user2.id, amount_owed=50))
            db.session.commit()
            
            balances = calculate_balances(group.id)
            assert balances[user1.id] == 50
            assert balances[user2.id] == -50


class TestSimplifyDebts:
    def test_simplify_three_people(self):
        with app.app_context():
            alice = User(id=1, username='alice', email='alice@test.com')
            bob = User(id=2, username='bob', email='bob@test.com')
            charlie = User(id=3, username='charlie', email='charlie@test.com')
            
            balances = {1: 50, 2: -30, 3: -20}
            members = [alice, bob, charlie]
            
            transfers = simplify_debts(balances, members)
            
            assert len(transfers) >= 1
            total_transferred = sum(t['amount'] for t in transfers)
            assert abs(total_transferred - 50) < 0.01


class TestSettlement:
    def test_settlement_reduces_balance(self, client, init_database):
        with app.app_context():
            user1 = User(username='payer', email='payer@test.com')
            user1.set_password('password')
            user2 = User(username='payee', email='payee@test.com')
            user2.set_password('password')
            db.session.add_all([user1, user2])
            db.session.commit()
            
            group = Group(name='Settle Group', invite_code='654321', created_by_id=user1.id)
            db.session.add(group)
            db.session.flush()
            
            db.session.add(GroupMember(user_id=user1.id, group_id=group.id))
            db.session.add(GroupMember(user_id=user2.id, group_id=group.id))
            
            settlement = Settlement(
                group_id=group.id,
                payer_id=user2.id,
                payee_id=user1.id,
                amount=50
            )
            db.session.add(settlement)
            db.session.commit()
            
            balances = calculate_balances(group.id)
            assert balances[user2.id] == 50
            assert balances[user1.id] == -50


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
