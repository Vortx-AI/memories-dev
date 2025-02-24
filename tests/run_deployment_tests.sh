#!/bin/bash

# Set up virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing test requirements..."
pip install -r requirements.txt

# Run all deployment tests
echo "Running deployment tests..."

echo "Running consensus deployment tests..."
pytest deployments/consensus/test_consensus_config.py -v

echo "Running swarmed deployment tests..."
pytest deployments/swarmed/test_swarmed_config.py -v

# Run with coverage report
echo "Running tests with coverage..."
pytest -v --cov=deployments \
    --cov-report=html:test-results/coverage \
    --cov-report=term-missing \
    --junitxml=test-results/junit.xml \
    deployments/

# Deactivate virtual environment
deactivate 