# SampleSplit

![Python](https://img.shields.io/badge/Python-3.11-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Tests](https://img.shields.io/badge/Tests-64%20passing-brightgreen.svg)
![Coverage](https://img.shields.io/badge/Coverage-86%25-green.svg)

A simple, privacy-first expense splitting app for groups of friends. Track shared expenses, split bills, and settle up easily. Self-hostable with no tracking or data sharing.

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app)

## Features

- **User Authentication** - Register and login with secure password hashing
- **Group Management** - Create groups with unique 6-digit invite codes, remove members (admin)
- **Multiple Split Methods**:
  - Equal split among selected members
  - Split by percentage (must total 100%)
  - Split by exact amounts
- **Balance Tracking** - Real-time balance calculations for each group member
- **Smart Settlements** - Simplified debt algorithm minimizes the number of payments needed
- **Categories** - Organize expenses with colored icons and custom budgets
- **Comments** - Discuss expenses with group members
- **Recurring Expenses** - Automate recurring payments (monthly rent, weekly groceries)
- **Dark Mode** - Built-in dark theme with toggle
- **Search & Filter** - Find expenses by description, filter by category, sort by date or amount
- **Export** - Download group expenses as PDF report
- **PWA** - Installable on mobile and desktop as a standalone app
- **Offline Fallback** - Graceful offline page when connectivity is lost

## Tech Stack

- **Backend**: Python 3.11+, Flask 3.0, SQLAlchemy
- **Database**: SQLite (default), PostgreSQL (production)
- **Frontend**: Bootstrap 5, Vanilla JavaScript
- **Auth**: Flask-Login with Werkzeug password hashing
- **Security**: Flask-WTF CSRF protection, rate limiting

---

## Installation

### Prerequisites

- Python 3.11 or higher
- Git

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/suprxsidh/sample-split.git
   cd sample-split
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app**
   ```bash
   python app.py
   ```

5. Open [http://localhost:8080](http://localhost:8080) in your browser.

### Resetting the Database

To start fresh:
```bash
rm -f samplesplit.db
```

---

## Deployment

### Docker Compose (Recommended for Production)

The fastest way to deploy with PostgreSQL:

```bash
cp .env.example .env
docker compose up -d
```

Open [http://localhost:8080](http://localhost:8080). PostgreSQL runs at `localhost:5432`.

### Railway (Recommended for Cloud Hosting)

1. Fork this repository to your GitHub account
2. Create a new project on [Railway](https://railway.app)
3. Connect your GitHub account
4. Select the `sample-split` repository
5. Add environment variables:
   - `SECRET_KEY`: Generate a random 32+ character string
   - `FLASK_ENV`: `production`
   - `DATABASE_URL`: (optional, Railway provides PostgreSQL automatically)
6. Deploy!

Railway automatically detects the Dockerfile and configures everything.

### Docker

**Build and run locally:**
```bash
docker build -t samplesplit .
docker run -p 8080:8080 \
  -e SECRET_KEY=your-secret-key \
  samplesplit
```

**Pull from Registry (if available):**
```bash
docker pull ghcr.io/suprxsidh/sample-split:latest
docker run -p 8080:8080 -e SECRET_KEY=your-secret-key ghcr.io/suprxsidh/sample-split:latest
```

### Render

1. Fork this repository
2. Create a new Web Service on [Render](https://render.com)
3. Connect your GitHub repository
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`
   - **Environment**: Python 3.11
5. Add environment variable: `SECRET_KEY` (generate a random string)
6. Add `DATABASE_URL` if using Render's PostgreSQL addon
7. Deploy!

### Fly.io

1. Install [flyctl](https://fly.io/docs/flyctl/install/)
2. Login: `fly auth login`
3. Create app: `fly launch`
4. Set secrets: `fly secrets set SECRET_KEY=your-secret-key`
5. Deploy: `fly deploy`

### Manual Production Deployment

```bash
# Set environment variables
export SECRET_KEY='your-secret-key-here'
export FLASK_ENV=production

# Run with gunicorn
gunicorn -b 0.0.0.0:8080 --workers 4 --threads 2 app:app
```

---

## Usage Guide

### Getting Started

1. **Register** - Create an account with username, email, and password
2. **Create a Group** - Give it a name
3. **Invite Friends** - Share the 6-digit invite code
4. **Add Expenses** - Record who paid and how to split it
5. **View Balances** - See who owes whom
6. **Settle Up** - Use the simplified debts view to minimize payments

### Split Methods

- **Equal Split**: Amount divided evenly among selected members
- **By Percentage**: Enter percentages (must total 100%)
- **By Exact Amounts**: Enter exact amounts for each member

### Categories

Create custom categories with icons and colors for better expense organization. Set budget limits per category to track spending.

---

## Test Accounts (Development)

After installing, create test accounts for development:

```bash
flask seed
```

This creates 4 users and 3 sample groups with realistic expenses:

| Username | Password | Groups |
|----------|----------|--------|
| alice | testpass123 | Weekend Trip, Dinner Club |
| bob | testpass123 | Weekend Trip, Roommates, Dinner Club |
| charlie | testpass123 | Weekend Trip, Roommates, Dinner Club |
| diana | testpass123 | Roommates, Dinner Club |

To reset: `rm -f samplesplit.db && flask seed`

---

## Project Structure

```
samplesplit/
├── app.py                  # Main Flask application and routes
├── models.py               # Database models (User, Group, Expense, etc.)
├── requirements.txt        # Python dependencies
├── Dockerfile              # Multi-stage production container
├── docker-compose.yml      # Docker Compose with PostgreSQL
├── .env.example           # Environment variable template
├── templates/              # Jinja2 HTML templates
│   ├── base.html          # Base layout template
│   ├── login.html         # Login page
│   ├── register.html      # Registration page
│   ├── dashboard.html     # User dashboard
│   ├── group.html         # Group details
│   ├── add_expense.html   # Add/edit expense
│   ├── settle_up.html     # Settlement view
│   └── admin_*.html       # Admin templates
├── static/
│   ├── style.css          # Custom styles
│   ├── manifest.json      # PWA manifest
│   ├── sw.js              # Service worker
│   ├── offline.html       # Offline fallback
│   └── icons/             # PWA icons
├── tests/                  # Pytest test suite
│   └── test_basic.py      # 64 unit tests
├── .github/
│   └── workflows/         # GitHub Actions CI/CD
│       └── ci.yml         # Continuous integration (SQLite + PostgreSQL)
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes (prod) | dev key | Flask secret key for sessions (32+ chars) |
| `FLASK_ENV` | No | `production` | `development` or `production` |
| `DATABASE_URL` | No | `sqlite:///samplesplit.db` | Database connection string |

### Database URL Examples

```bash
# SQLite (default, local development)
DATABASE_URL=sqlite:///samplesplit.db

# PostgreSQL (production)
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/samplesplit

# PostgreSQL on Railway/Render
DATABASE_URL=postgresql+psycopg://user:pass@host:port/database?sslmode=require
```

### Generating a Secret Key

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=. --cov-report=term

# Generate HTML coverage report
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html
```

---

## Contributing

Contributions welcome! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Code Style

- **Python**: PEP 8, 4-space indentation, max 120 line length
- **Naming**: `snake_case` (variables), `PascalCase` (classes), `UPPER_SNAKE` (constants)
- **Formatting**: Black code formatter
- **Linting**: Flake8

### Submitting Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Run tests: `pytest tests/ -v`
5. Format code: `black .`
6. Lint: `flake8 app.py models.py tests/`
7. Submit a pull request

---

## Philosophy

- **Simple first** - Core features work flawlessly before adding complexity
- **User-owned** - Self-hostable, no lock-in
- **Privacy-first** - No tracking, no data sharing

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Bootstrap](https://getbootstrap.com/) - Frontend toolkit
- [Splitwise](https://www.splitwise.com/) - Inspiration
