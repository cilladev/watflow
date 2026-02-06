# Contributing to WATFlow

Thank you for your interest in contributing to WATFlow!

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/cilladev/watflow.git
   cd watflow
   ```

2. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Install dependencies:**
   ```bash
   poetry install --with dev
   ```

4. **Set up pre-commit hooks:**
   ```bash
   poetry run pre-commit install
   ```

5. **Activate the virtual environment:**
   ```bash
   poetry shell
   ```

## Pre-commit Hooks

We use pre-commit to ensure code quality. The hooks run automatically on every commit:

- **Ruff Check** - Linting with auto-fix
- **Ruff Format** - Code formatting
- **Trailing whitespace** - Remove trailing whitespace
- **End of file fixer** - Ensure files end with newline
- **Check YAML** - Validate YAML syntax
- **Check large files** - Prevent large files from being committed
- **Check merge conflict** - Detect merge conflict markers

To run hooks manually on all files:

```bash
poetry run pre-commit run --all-files
```

## Running Tests

```bash
poetry run pytest
```

## Code Style

We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Check for issues
poetry run ruff check .

# Auto-fix issues
poetry run ruff check --fix .

# Format code
poetry run ruff format .
```

## Type Checking

```bash
poetry run mypy watflow
```

## Making Changes

1. Create a new branch for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and ensure tests pass

3. Commit your changes (pre-commit hooks will run automatically)

4. Push to your fork and create a pull request

## Pull Request Guidelines

- Keep PRs focused on a single feature or fix
- Include tests for new functionality
- Update documentation if needed
- Ensure all tests pass before submitting
- Pre-commit hooks must pass

## Reporting Issues

When reporting issues, please include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior

## Questions?

Feel free to open an issue for any questions about contributing.
