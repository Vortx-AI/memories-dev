#!/bin/bash

# Set up virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Run tests with pytest
echo "Running tests..."
pytest -v --cov=deployments \
    --cov-report=html:test-results/coverage \
    --cov-report=term-missing \
    --junitxml=test-results/junit.xml \
    "$@"

# Deactivate virtual environment
deactivate 