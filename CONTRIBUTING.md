# Contributing to SampleSplit

Thank you for your interest in contributing to SampleSplit! This document provides guidelines and instructions for contributing.

---

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd samplesplit
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the development server**
   ```bash
   python app.py
   ```

   The app will be available at `http://localhost:8080`.

### Resetting the Database

To start with a fresh database:
```bash
rm -f samplesplit.db
```

---

## Running Tests

The project uses pytest for testing.

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run a specific test file
pytest tests/test_basic.py -v

# Run tests matching a pattern
pytest tests/ -k "test_register"
```

---

## Code Style

Please follow the code style guidelines defined in [AGENTS.md](./AGENTS.md).

### Key Points

- **Indentation**: 4 spaces (no tabs)
- **Line length**: Maximum 120 characters
- **Naming conventions**:
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

### JavaScript

- Vanilla JS only (no frameworks)
- ES6+ syntax (const, let, arrow functions)
- camelCase for function names

### HTML Templates

- Extend `base.html`
- Use `{% block %}` for sections
- Bootstrap 5 classes for styling

---

## Git Workflow

### 1. Create a Branch

Create a new branch for your feature or fix:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Changes

1. Write your code following the style guidelines
2. Add tests for new functionality
3. Ensure tests pass

### 3. Commit Your Changes

Write clear, concise commit messages:

```bash
git add .
git commit -m "Add feature description"
```

**Commit message guidelines**:
- Use present tense ("Add feature" not "Added feature")
- First line should be 50 characters or less
- Add detailed description in subsequent lines if needed

### 4. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear title describing the change
- Description of what was changed and why
- Reference any related issues

---

## Types of Contributions Welcome

### Bug Fixes

- Fix incorrect balance calculations
- Fix settlement logic errors
- Fix UI/UX issues
- Improve error handling

### Features

- Additional split methods (percentages, shares, etc.)
- Currency support beyond INR
- Export functionality (CSV, PDF)
- Email/push notifications
- Group categories or tags
- Search and filtering

### Improvements

- Enhanced balance simplification algorithm
- Better input validation
- Improved accessibility
- Performance optimizations

### Documentation

- Improve code comments
- Add usage examples
- Improve this contributing guide

### Testing

- Add more test coverage
- Edge case testing
- Integration tests

---

## Questions?

Feel free to open an issue for questions or discussions about potential contributions.
