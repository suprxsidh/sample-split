# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-03-21

### Added
- **PWA support** - Installable as standalone app on mobile and desktop, offline fallback page, service worker caching
- **PostgreSQL support** - Via `psycopg[binary]` driver, works with Railway, Render, Docker Compose
- **Docker Compose** - Full stack with PostgreSQL 16, health checks, persistent volume
- **Multi-stage Dockerfile** - Non-root user, tuned gunicorn (4 workers, 2 threads), health checks
- **Test accounts CLI** - `flask seed` creates 4 users and 3 sample groups with realistic expenses
- **.env.example** - Template with PostgreSQL connection strings for all major platforms

### Changed
- Upgraded `psycopg2-binary` → `psycopg[binary]` for PostgreSQL (pure Python, no system libs)

### Fixed
- **SQLAlchemy 2.0 deprecations** - `Model.query.get()` → `db.session.get()`, `Model.query.get_or_404()` → `db.get_or_404()`
- **datetime.utcnow() deprecation** - Replaced with `datetime.now(timezone.utc)` in app.py and models.py
- **Dead code cleanup** - Removed unused `members` parameter in `simplify_debts()`, redundant imports, unused `group_obj` variables
- **Duplicate test class** - Renamed `TestBudget` → `TestBudgetEdgeCases`

### Testing
- **64 tests passing** (was 9)
- **86% code coverage** (was 81%)
- New tests: exact split, percentage validation, expense dates, budget edge cases, simplify debts edge cases, forgot password, settlement flow
- CI pipeline: SQLite tests + PostgreSQL integration tests

## [0.4.0] - 2026-03-21

### Added
- Complete README with installation guide
- Deployment guides (Railway, Render, Fly.io, Docker)
- SECURITY.md
- Demo screenshots/GIFs (deferred - friends testing UI)

### Code Quality
- Automated tests (>80% coverage) - 81% coverage
- Security audit (basic)
- Code formatter (black)
- Linting (flake8)
- CI/CD pipeline (GitHub Actions)

### Community
- CONTRIBUTING.md
- CODE_OF_CONDUCT.md
- Issue templates
- Pull request template

## [0.3.0] - 2026-03-21

### Added
- GitHub repository (suprxsidh/sample-split)
- `.gitignore` file for Python/Flask
- `LICENSE` file (MIT)
- README.md documentation with deployment instructions
- Dockerfile for containerization
- CONTRIBUTING.md for developers
- Basic pytest test suite (9 tests)
- Railway deployment configuration

### Security
- Flask-WTF CSRF protection on all forms
- Rate limiting on authentication routes (login: 10/min, register: 5/min, admin: 3/min)

### Fixed
- Database initialization on app startup for production

## [0.2.0] - 2026-03-20

### Added
- Split expenses by percentage (must total 100%)
- Split expenses by exact amounts
- Expense date picker for backdated expenses
- Search expenses by description
- Delete expense (creator only)
- Edit group name
- Leave group functionality
- Copy invite code to clipboard

## [0.1.0] - 2026-03-19

### Added
- User registration and login
- Create groups with 6-digit invite codes
- Join groups via invite code
- Add expenses with equal split among selected members
- View group balances
- Record settlements between members
- Simplify debts algorithm for minimum transfers
- Dark mode toggle
