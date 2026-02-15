# https://just.systems

default:
    @just --list

# Run tests with pytest
test:
    PYTHONPATH=lib ./venv/bin/pytest -v

# Run tests with coverage
test-coverage:
    PYTHONPATH=lib ./venv/bin/pytest --cov=lib --cov-report=term-missing

# Run specific test file
test-file FILE:
    PYTHONPATH=lib ./venv/bin/pytest -v {{FILE}}

# Format with ruff
format:
    ./venv/bin/ruff format .

# Lint with ruff
lint:
    ./venv/bin/ruff check .

# Lint with ruff and auto-fix
lint-fix:
    ./venv/bin/ruff check . --fix

# Type check with mypy
typecheck:
    ./venv/bin/mypy lib test

# Install dependencies
install:
    ./venv/bin/pip install -r requirements.txt

# Install dev dependencies
install-dev:
    ./venv/bin/pip install -r requirements-dev.txt

# Run all checks, format and tests
all: lint-fix format typecheck test

# Start the challenge server
run:
    PYTHONPATH=lib ./venv/bin/python lib/send_command_to_server.py
