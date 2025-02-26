#!/bin/bash

# Script to test the documentation build with the new requirements file

# Set up colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Testing documentation build with optimized requirements...${NC}"

# Navigate to the docs directory
cd "$(dirname "$0")"

# Make sure we're in the docs directory
if [ ! -f "Makefile" ]; then
  echo -e "${RED}Error: Must be run from the docs directory${NC}"
  exit 1
fi

# Create a temporary virtual environment
echo -e "${YELLOW}Creating temporary virtual environment...${NC}"
python -m venv temp_venv
source temp_venv/bin/activate

# Install the dependencies from the minimal requirements file
echo -e "${YELLOW}Installing dependencies from requirements-docs.txt...${NC}"
pip install -r requirements-docs.txt

# Build the HTML documentation
echo -e "${YELLOW}Building HTML documentation...${NC}"
make html

# Check if the build was successful
if [ $? -eq 0 ]; then
  echo -e "${GREEN}Documentation built successfully!${NC}"
  echo -e "${GREEN}Output is in: $(pwd)/build/html/index.html${NC}"
  
  # Open the documentation if on macOS
  if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${YELLOW}Opening documentation in browser...${NC}"
    open build/html/index.html
  fi
else
  echo -e "${RED}Documentation build failed!${NC}"
  exit 1
fi

# Build the PDF documentation as a further test
echo -e "${YELLOW}Building PDF documentation...${NC}"

# Check for required PDF build tools
if ! command -v pdflatex &> /dev/null; then
    echo -e "${YELLOW}Warning: pdflatex not found, skipping PDF build${NC}"
elif ! command -v latexmk &> /dev/null; then
    echo -e "${YELLOW}Warning: latexmk not found, skipping PDF build${NC}"
else
    make latexpdf || make rst2pdf || echo -e "${YELLOW}Warning: PDF build failed, continuing with other tests${NC}"
fi

# Cleanup
echo -e "${YELLOW}Cleaning up...${NC}"
if [ -d "temp_venv" ]; then
    deactivate
    rm -rf temp_venv
fi

# Clean build artifacts
make clean || echo -e "${YELLOW}Warning: Clean failed, please check build directory${NC}"

echo -e "${GREEN}Test complete!${NC}"
echo ""
echo -e "${YELLOW}To build documentation in your main environment:${NC}"
echo "  1. cd docs"
echo "  2. pip install -r requirements-docs.txt"
echo "  3. make html"
echo ""
echo -e "${YELLOW}For a more permanent setup:${NC}"
echo "  make setup   # Installs all required dependencies"
echo "  make html    # Builds HTML documentation"
echo "" 