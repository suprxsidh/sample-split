# SampleSplit - Agent Guidelines

This document provides guidance for agents working on the SampleSplit codebase.

---

## Project Overview

SampleSplit is a Flask-based expense splitting application for groups of friends. It allows users to create groups, add expenses with various split methods, track balances, and settle up.

**Stack**: Python 3, Flask, SQLAlchemy, SQLite, Bootstrap 5, Vanilla JS

---

## Build Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server (port 8080)
source venv/bin/activate
python app.py

# Reset database (clears all data)
rm -f samplesplit.db

# Start with tunnel (for testing with friends)
./start.sh
# Choose option 3 for public URL
```

---

## Code Style

### Python Style
- **Indentation**: 4 spaces (no tabs)
- **Line length**: Max 120 characters
- **Naming**:
  - `snake_case` for variables and functions
  - `PascalCase` for classes
  - `UPPER_SNAKE` for constants
- **Quotes**: Double quotes preferred
- **Type hints**: Use where helpful, especially function signatures
- **Docstrings**: Google style for functions

### Import Order
1. Standard library
2. Third-party packages
3. Local imports
4. Blank line between groups

### Example
```python
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, User, Group

def calculate_balances(group_id):
    """Calculate net balances for all group members."""
    balances = {}
    # ... logic
    return balances
```

### HTML Templates (Jinja2)
- Extend `base.html`
- Use `{% block %}` for sections
- Bootstrap 5 classes for styling
- Semantic HTML elements
- `data-bs-theme` attribute for dark mode toggle

### JavaScript
- Vanilla JS only (no frameworks)
- ES6+ syntax (const, let, arrow functions)
- camelCase for function names
- Defer scripts or place at end of body

---

## Architecture

### Database Models (`models.py`)

| Model | Purpose |
|-------|---------|
| `User` | User accounts with password hashing |
| `Group` | Expense groups with 6-digit invite codes |
| `GroupMember` | Many-to-many relationship between users and groups |
| `Expense` | Expenses with payer, amount, description, date |
| `ExpenseSplit` | Individual amounts owed per user per expense |
| `Settlement` | Records of payments between users |

### Route Pattern
```python
@app.route('/path/<int:id>', methods=['GET', 'POST'])
@login_required
def route_name(id):
    # 1. Get and validate object
    # 2. Check membership/permissions
    # 3. Process form data if POST
    # 4. Commit to database
    # 5. Flash message and redirect
```

### Key Functions
- `calculate_balances(group_id)` - Returns dict of user_id → net balance
- `simplify_debts(balances, members)` - Returns minimum transfer list

---

## Frontend Conventions

### Dark Mode
- Use `data-bs-theme="light|dark"` on `<html>`
- Toggle via `localStorage.getItem('theme')`
- CSS variables for theme-aware colors

### Colors
| Meaning | Color |
|---------|-------|
| Positive balance (gets back) | Green (#22c55e) |
| Negative balance (owes) | Red (#ef4444) |
| Primary actions | Green buttons |

### Currency
- Always display as INR (₹ symbol)
- Amounts stored as floats, formatted with 2 decimal places

---

## Common Tasks

### Adding a New Route
1. Add `@app.route()` decorator
2. Use `@login_required` if auth needed
3. Get objects from database
4. Validate user access
5. Process form with error handling
6. Flash message and redirect

### Adding a Template
1. Create HTML file in `templates/`
2. Extend `base.html`
3. Define `{% block title %}` and `{% block content %}`
4. Add `{% block scripts %}` for JS if needed

### Modifying Database
1. Update `models.py`
2. Delete `samplesplit.db` to recreate tables
3. Test with fresh data

---

## Testing

Currently no formal test suite. To test manually:

1. Register two test users
2. Create a group
3. Add expenses with different split types
4. Verify balances calculate correctly
5. Test settlements
6. Test simplify debts algorithm

### Manual Test Scenario
```python
# Create 2 users, 1 group
# User A pays ₹100 dinner (split 2 ways)
# Balance: A = +50, B = -50
# B pays A ₹50
# Balance: A = 0, B = 0
```

---

## Security Notes

- Passwords hashed with Werkzeug
- Admin credentials in `app.py` (env var in production)
- Session-based auth via Flask-Login
- Check membership before group operations

---

## File Structure

```
samplesplit/
├── app.py              # Main Flask app, routes
├── models.py           # SQLAlchemy models
├── requirements.txt    # Python dependencies
├── samplesplit.db     # SQLite database
├── start.sh           # Startup script
├── ROADMAP.md         # Future plans
├── templates/
│   ├── base.html      # Layout template
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── group.html
│   ├── add_expense.html
│   ├── settle_up.html
│   └── admin_*.html
└── static/
    └── style.css       # Custom styles
```

---

## Important Notes

- App runs on port 8080 (not 5000 - avoid macOS AirPlay conflict)
- Group invite codes are 6 digits
- Settlements reduce the amount owed (payer balance increases)
- Simplify debts uses greedy algorithm for minimum transfers
- Expense creator can delete their own expenses only
