# https://just.systems

default:
    echo 'Hello, world!'

# Run tests with pytest
test:
    ./venv/bin/pytest

# Run tests with coverage
test-coverage:
    ./venv/bin/pytest --cov=lib --cov-report=term-missing

# Run specific test file
test-file FILE:
    ./venv/bin/pytest {{FILE}}

# Install dependencies
install:
    ./venv/bin/pip install -r requirements.txt

# Run all checks and tests
all: test
