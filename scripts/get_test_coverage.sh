#!/bin/bash

# Install necessary dependencies
pip install coverage pytest

# Run tests with coverage
coverage run -m pytest

# Generate coverage report in terminal
coverage report

# Generate HTML coverage report
coverage html

# Open the HTML coverage report (adjust the command based on your OS)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open htmlcov/index.html
elif [[ "$OSTYPE" == "darwin"* ]]; then
    open htmlcov/index.html
elif [[ "$OSTYPE" == "cygwin" ]]; then
    cygstart htmlcov/index.html
elif [[ "$OSTYPE" == "msys" ]]; then
    start htmlcov/index.html
elif [[ "$OSTYPE" == "win32" ]]; then
    start htmlcov/index.html
else
    echo "Please open htmlcov/index.html manually"
fi