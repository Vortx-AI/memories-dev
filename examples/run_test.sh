#!/bin/bash

# Get the absolute path to the project root directory
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"

# Add the project root to PYTHONPATH
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

# Run the test script with all arguments passed to this script
python3 "${PROJECT_ROOT}/examples/test_remote_query.py" "$@" 