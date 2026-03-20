# SampleSplit

A simple, privacy-first expense splitting app for groups of friends. Track shared expenses, split bills, and settle up easily.

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app)

## Features

- **User Authentication** - Register and login to manage your expenses
- **Group Management** - Create groups with unique 6-digit invite codes
- **Multiple Split Methods**:
  - Equal split among selected members
  - Split by percentage (must total 100%)
  - Split by exact amounts
- **Balance Tracking** - Real-time balance calculations for each group member
- **Smart Settlements** - Simplified debt algorithm minimizes the number of payments needed
- **Dark Mode** - Built-in dark theme support
- **Search** - Find expenses quickly within groups
- **Expense Management** - Edit dates, delete your own expenses

## Tech Stack

- **Backend**: Python 3, Flask, SQLAlchemy
- **Database**: SQLite (PostgreSQL-ready for scaling)
- **Frontend**: Bootstrap 5, Vanilla JavaScript
- **Auth**: Flask-Login with secure password hashing

## Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/suprxsidh/sample-split.git
cd sample-split

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Open [http://localhost:8080](http://localhost:8080) in your browser.

### Docker

```bash
# Build and run
docker build -t samplesplit .
docker run -p 8080:8080 samplesplit
```

## Deployment

### Railway (Recommended)

1. Fork this repository
2. Create a new project on [Railway](https://railway.app)
3. Connect your GitHub account
4. Select the `sample-split` repository
5. Add a `SECRET_KEY` environment variable (generate a random 32+ character string)
6. Deploy!

Railway will automatically detect the Dockerfile and configure everything.

### Manual Deployment

Set environment variables and run with gunicorn:

```bash
export SECRET_KEY='your-secret-key-here'
export FLASK_ENV=production
gunicorn -b 0.0.0.0:8080 app:app
```

## Project Structure

```
samplesplit/
├── app.py              # Main Flask application and routes
├── models.py           # Database models
├── requirements.txt    # Python dependencies
├── templates/          # Jinja2 HTML templates
├── static/            # CSS and static assets
├── tests/             # Pytest test suite
├── Dockerfile         # Production container
└── LICENSE            # MIT License
```

## Usage

1. **Register** - Create an account with username, email, and password
2. **Create a Group** - Give it a name and share the 6-digit invite code
3. **Add Friends** - They join using the invite code
4. **Add Expenses** - Record who paid and how to split it
5. **Settle Up** - Use the simplified debts view to minimize payments

## Philosophy

- **Simple first** - Core features work flawlessly before adding complexity
- **User-owned** - Self-hostable, no lock-in
- **Privacy-first** - No tracking, no data sharing

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please read the existing code style in `AGENTS.md` and submit a pull request.
