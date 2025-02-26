# Minimal makefile for Sphinx documentation

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile singlelatex singlelatexpdf rtd-pdf setup

# Setup the documentation environment
setup:
	@echo "Setting up documentation environment..."
	@pip install -r requirements-docs.txt
	@echo "Documentation dependencies installed successfully!"

# Special target for ReadTheDocs - ensures only one PDF is generated
rtd-pdf:
	@$(SPHINXBUILD) -M latex "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@cd "$(BUILDDIR)/latex" && latexmk -silent -pdf memories-dev.tex
	@mkdir -p _readthedocs/pdf
	@cp "$(BUILDDIR)/latex/memories-dev.pdf" _readthedocs/pdf/

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O) 
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
