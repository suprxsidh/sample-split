# SampleSplit

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Tests](https://img.shields.io/badge/Tests-9%20passing-brightgreen.svg)

A simple, privacy-first expense splitting app for groups of friends. Track shared expenses, split bills, and settle up easily. Self-hostable with no tracking or data sharing.

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app)

## Features

- **User Authentication** - Register and login with secure password hashing
- **Group Management** - Create groups with unique 6-digit invite codes
- **Multiple Split Methods**:
  - Equal split among selected members
  - Split by percentage (must total 100%)
  - Split by exact amounts
- **Balance Tracking** - Real-time balance calculations for each group member
- **Smart Settlements** - Simplified debt algorithm minimizes the number of payments needed
- **Dark Mode** - Built-in dark theme with toggle
- **Search** - Find expenses quickly within groups
- **Expense Management** - Edit dates, delete your own expenses
- **Leave/Edit Groups** - Full group management capabilities

## Tech Stack

- **Backend**: Python 3.10+, Flask 3.0, SQLAlchemy
- **Database**: SQLite (PostgreSQL-ready for scaling)
- **Frontend**: Bootstrap 5, Vanilla JavaScript
- **Auth**: Flask-Login with Werkzeug password hashing
- **Security**: Flask-WTF CSRF protection, rate limiting

---

## Installation

### Prerequisites

- Python 3.10 or higher
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

### Railway (Recommended)

The easiest way to deploy SampleSplit.

1. Fork this repository to your GitHub account
2. Create a new project on [Railway](https://railway.app)
3. Connect your GitHub account
4. Select the `sample-split` repository
5. Add environment variables:
   - `SECRET_KEY`: Generate a random 32+ character string
   - `FLASK_ENV`: `production`
6. Deploy!

Railway automatically detects the Dockerfile and configures everything.

### Render

1. Fork this repository
2. Create a new Web Service on [Render](https://render.com)
3. Connect your GitHub repository
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`
   - **Environment**: Python 3
5. Add environment variable: `SECRET_KEY` (generate a random string)
6. Deploy!

### Fly.io

1. Install [flyctl](https://fly.io/docs/flyctl/install/)
2. Login: `fly auth login`
3. Create app: `fly launch`
4. Set secrets: `fly secrets set SECRET_KEY=your-secret-key`
5. Deploy: `fly deploy`

### Docker

**Build and run locally:**
```bash
docker build -t samplesplit .
docker run -p 8080:8080 \
  -e SECRET_KEY=your-secret-key \
  samplesplit
```

**Using Docker Compose:**
```yaml
services:
  web:
    build: .
    ports:
      - "8080:8080"
    environment:
      - SECRET_KEY=your-secret-key
      - FLASK_ENV=production
```

**Pull from Registry (if available):**
```bash
docker pull ghcr.io/suprxsidh/sample-split:latest
docker run -p 8080:8080 -e SECRET_KEY=your-secret-key ghcr.io/suprxsidh/sample-split:latest
```

### Manual Production Deployment

```bash
# Set environment variables
export SECRET_KEY='your-secret-key-here'
export FLASK_ENV=production

# Run with gunicorn
gunicorn -b 0.0.0.0:8080 --workers 2 app:app
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

---

## Project Structure

```
samplesplit/
├── app.py                  # Main Flask application and routes
├── models.py               # Database models (User, Group, Expense, etc.)
├── requirements.txt       # Python dependencies
├── Dockerfile              # Production container
├── docker-compose.yml      # Docker Compose configuration
├── pyproject.toml          # Black and Flake8 configuration
├── .flake8                 # Flake8 linting configuration
├── templates/              # Jinja2 HTML templates
│   ├── base.html          # Base layout template
│   ├── login.html         # Login page
│   ├── register.html     # Registration page
│   ├── dashboard.html     # User dashboard
│   ├── group.html         # Group details
│   ├── add_expense.html   # Add/edit expense
│   ├── settle_up.html     # Settlement view
│   └── admin_*.html       # Admin templates
├── static/
│   └── style.css          # Custom styles
├── tests/                  # Pytest test suite
│   └── test_basic.py      # Unit tests
├── .github/
│   └── workflows/         # GitHub Actions CI/CD
│       └── ci.yml         # Continuous integration
└── docs/                   # Deployment guides
    └── DEPLOYMENT.md       # Detailed deployment instructions
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | - | Flask secret key for sessions (32+ chars) |
| `FLASK_ENV` | No | `production` | `development` or `production` |
| `DATABASE_URL` | No | `samplesplit.db` | SQLite database path |

### Generating a Secret Key

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_basic.py -v

# Run with coverage
pytest tests/ -v --cov=. --cov-report=html
```

---

## Contributing

Contributions welcome! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Code Style

- **Python**: PEP 8, 4-space indentation, max 120 line length
- **Naming**: `snake_case` (variables), `PascalCase` (classes), `UPPER_SNAKE` (constants)
- **Formatting**: Black code formatter (configured in `pyproject.toml`)
- **Linting**: Flake8 (configured in `.flake8`)

### Submitting Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Run tests: `pytest tests/ -v`
5. Format code: `black .`
6. Submit a pull request

---

## Philosophy

- **Simple first** - Core features work flawlessly before adding complexity
- **User-owned** - Self-hostable, no lock-in
- **Privacy-first** - No tracking, no data sharing

---

## Screenshots

*(Add screenshots here after development)*

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Bootstrap](https://getbootstrap.com/) - Frontend toolkit
- [Splitwise](https://www.splitwise.com/) - Inspiration
