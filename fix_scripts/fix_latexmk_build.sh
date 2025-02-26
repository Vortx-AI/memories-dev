#!/bin/bash
# Fix LaTeX PDF build issues for ReadTheDocs
# This script ensures proper directory structure and fixes build commands

set -e  # Exit on error

# Ensure we're in the project root
cd "$(dirname "$0")/.." || exit 1
PROJECT_ROOT=$(pwd)
echo "Project root: $PROJECT_ROOT"

# Create a simplified latexmkrc file
cat > docs/latexmkrc << 'EOF'
$pdflatex = 'pdflatex -interaction=nonstopmode -halt-on-error %O %S';
$pdf_mode = 1;
$dvi_mode = 0;
$postscript_mode = 0;
EOF

echo "Created simplified latexmkrc file"

# Create a custom Makefile target for RTD
cat >> docs/Makefile << 'EOF'

# Special target for ReadTheDocs that works around PDF build issues
rtd-latexpdf:
	@echo "Building PDF for ReadTheDocs..."
	@$(SPHINXBUILD) -M latex "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@cd "$(BUILDDIR)/latex" && \
	sed -i 's/\\usepackage{sphinx}/\\usepackage[final]{sphinx}/g' memories-dev.tex && \
	sed -i 's/\\usepackage{graphicx}/\\usepackage{graphicx}\\usepackage{xcolor}/g' memories-dev.tex && \
	pdflatex -interaction=nonstopmode memories-dev.tex && \
	pdflatex -interaction=nonstopmode memories-dev.tex && \
	pdflatex -interaction=nonstopmode memories-dev.tex
	@echo "PDF built at $(BUILDDIR)/latex/memories-dev.pdf"
	@mkdir -p _readthedocs/html/
	@cp "$(BUILDDIR)/latex/memories-dev.pdf" _readthedocs/html/
EOF

echo "Added rtd-latexpdf target to Makefile"

# Update .readthedocs.yaml to use the new approach
sed -i.bak 's/- cd docs && make latexpdf/- cd docs \&\& make rtd-latexpdf/g' .readthedocs.yaml
echo "Updated .readthedocs.yaml to use rtd-latexpdf"

# Fix any remaining LaTeX syntax issues in the generated .tex file
fix_latex_syntax() {
    if [ -f "docs/build/latex/memories-dev.tex" ]; then
        echo "Fixing LaTeX syntax in memories-dev.tex..."
        # Fix any problematic math commands
        sed -i 's/\\text{\\([a-zA-Z0-9_]*\\)}/\\1/g' docs/build/latex/memories-dev.tex
        # Fix underscores in text
        sed -i 's/\\text{\\([a-zA-Z0-9]*\\)_\\([a-zA-Z0-9]*\\)}/\\text{\\1\\_\\2}/g' docs/build/latex/memories-dev.tex
        # Make sure Graphics package is loaded
        sed -i 's/\\begin{document}/\\usepackage{graphicx}\\usepackage{xcolor}\\begin{document}/g' docs/build/latex/memories-dev.tex
        echo "LaTeX syntax fixed"
    else
        echo "memories-dev.tex not found. Run 'cd docs && make latex' first."
    fi
}

# Run the previous fix scripts first
echo "Running fix_txt_diagrams.py..."
python fix_scripts/fix_txt_diagrams.py

echo "Running fix_math_equations.py..."
python fix_scripts/fix_math_equations.py

# Try to build the docs with the new setup
echo "Attempting to build the PDF..."
cd docs || exit 1
make clean
make latex
fix_latex_syntax
cd build/latex || exit 1
latexmk -pdf -interaction=nonstopmode -shell-escape memories-dev.tex

echo "If successful, PDF should be at: docs/build/latex/memories-dev.pdf"
echo "You can now try: cd docs && make rtd-latexpdf" 