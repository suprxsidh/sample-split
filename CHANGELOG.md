# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- User profile management
- Email notifications
- Expense categories and tags
- Export expenses to CSV

## [0.3.0] - 2026-03-21

### Added
- GitHub repository setup
- `.gitignore` file for Python/Flask
- `LICENSE` file (MIT)
- `README.md` documentation
- `Dockerfile` for containerization
- Basic pytest test suite
- Railway deployment configuration

### Security
- Flask-WTF CSRF protection on all forms
- Rate limiting on authentication routes (login/register)

## [0.2.0] - 2026-03-???

### Added
- Split expenses by percentage (must total 100%)
- Split expenses by exact amounts
- Expense date picker for backdated expenses
- Search expenses by description
- Delete expense (creator only)
- Edit group name
- Leave group functionality
- Copy invite code to clipboard

## [0.1.0] - 2026-03-???

### Added
- User registration and login
- Create groups with 6-digit invite codes
- Join groups via invite code
- Add expenses with equal split among selected members
- View group balances
- Record settlements between members
- Simplify debts algorithm for minimum transfers
- Dark mode toggle
