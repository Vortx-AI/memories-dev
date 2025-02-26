// Formula Enhancer for memories-dev documentation
document.addEventListener('DOMContentLoaded', function() {
    // Initialize formula enhancer once MathJax is loaded
    if (window.MathJax) {
        initializeFormulaEnhancer();
    } else {
        // Wait for MathJax to load
        window.addEventListener('load', function() {
            setTimeout(initializeFormulaEnhancer, 500);
        });
    }
});

/**
 * Initialize the formula enhancer component
 */
function initializeFormulaEnhancer() {
    // Configure MathJax if available
    configureMathJax();
    
    // Add formula styles
    addFormulaStyles();
    
    // Enhance formula display
    enhanceFormulaDisplay();
    
    // Add copy button to formulas
    addCopyButtonToFormulas();
    
    // Fix formula rendering issues
    fixFormulaRenderingIssues();

    // Add equation numbering
    addEquationNumbering();
}

/**
 * Configure MathJax for better formula rendering
 */
function configureMathJax() {
    if (window.MathJax) {
        // For MathJax v3
        if (window.MathJax.version && window.MathJax.version[0] === '3') {
            // Check if already configured
            if (window.MathJax.startup && window.MathJax.startup._initialized) {
                return;
            }
            
            // Configure MathJax
            window.MathJax = {
                tex: {
                    inlineMath: [['$', '$'], ['\\(', '\\)']],
                    displayMath: [['$$', '$$'], ['\\[', '\\]']],
                    processEscapes: true,
                    processEnvironments: true,
                    tags: 'ams',
                    packages: ['base', 'ams', 'noerrors', 'noundefined', 'color', 'boldsymbol']
                },
                options: {
                    ignoreHtmlClass: 'tex2jax_ignore',
                    processHtmlClass: 'tex2jax_process'
                },
                chtml: {
                    scale: 1.1,
                    displayAlign: 'center'
                },
                startup: {
                    ready: function() {
                        window.MathJax.startup.defaultReady();
                        enhanceFormulaDisplay();
                    }
                }
            };
        } 
        // For MathJax v2
        else if (window.MathJax.Hub) {
            window.MathJax.Hub.Config({
                tex2jax: {
                    inlineMath: [['$', '$'], ['\\(', '\\)']],
                    displayMath: [['$$', '$$'], ['\\[', '\\]']],
                    processEscapes: true,
                    processEnvironments: true
                },
                TeX: {
                    equationNumbers: { autoNumber: "AMS" },
                    extensions: ["color.js", "AMSmath.js", "AMSsymbols.js", "noErrors.js", "noUndefined.js"]
                },
                'HTML-CSS': {
                    availableFonts: ['TeX'],
                    scale: 110,
                    linebreaks: { automatic: true }
                },
                SVG: {
                    linebreaks: { automatic: true }
                }
            });
            
            window.MathJax.Hub.Register.StartupHook('End', function() {
                enhanceFormulaDisplay();
            });
        }
    }
}

/**
 * Add styles for formula rendering
 */
function addFormulaStyles() {
    const style = document.createElement('style');
    style.textContent = `
        /* Formula container */
        .formula-container {
            margin: 1.5rem 0;
            position: relative;
            overflow-x: auto;
            padding: 1rem;
            background-color: var(--code-bg, #f8f9fa);
            border-radius: 4px;
            border-left: 3px solid var(--accent-color, #3b82f6);
        }
        
        /* Inline formula */
        .math {
            display: inline-block;
            vertical-align: middle;
            max-width: 100%;
            overflow-x: auto;
            padding: 0 0.2em;
        }
        
        /* Display formula */
        .math-display {
            display: block;
            overflow-x: auto;
            max-width: 100%;
            margin: 1rem 0;
            text-align: center;
        }
        
        /* Formula copy button */
        .formula-copy-btn {
            position: absolute;
            top: 0.25rem;
            right: 0.25rem;
            background-color: transparent;
            border: none;
            padding: 0.25rem;
            cursor: pointer;
            font-size: 0.8rem;
            color: var(--code-text-muted, #6c757d);
            border-radius: 3px;
            opacity: 0;
            transition: opacity 0.2s, background-color 0.2s;
        }
        
        .formula-container:hover .formula-copy-btn {
            opacity: 1;
        }
        
        .formula-copy-btn:hover {
            background-color: var(--accent-light, #dbeafe);
            color: var(--accent-color, #3b82f6);
        }
        
        /* Equation numbering */
        .equation-number {
            float: right;
            color: var(--code-text-muted, #6c757d);
            font-size: 0.9rem;
        }
        
        /* Dark mode support */
        html.dark-theme .formula-container {
            background-color: var(--code-bg, #1e293b);
            border-left-color: var(--accent-color, #3b82f6);
        }
        
        html.dark-theme .formula-copy-btn:hover {
            background-color: var(--accent-dark, #1e40af);
            color: var(--accent-light, #dbeafe);
        }
        
        /* Formula loading state */
        .formula-loading {
            display: inline-block;
            width: 1em;
            height: 1em;
            vertical-align: middle;
            border: 2px solid var(--accent-light, #dbeafe);
            border-top: 2px solid var(--accent-color, #3b82f6);
            border-radius: 50%;
            animation: formula-spin 1s linear infinite;
        }
        
        @keyframes formula-spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
}

/**
 * Enhance formula display with custom styling
 */
function enhanceFormulaDisplay() {
    // Find all math display containers
    const mathElements = document.querySelectorAll('.math-display, .math');
    
    mathElements.forEach(element => {
        const isDisplayMath = element.classList.contains('math-display');
        
        // Skip if already enhanced
        if (element.parentElement.classList.contains('formula-container')) {
            return;
        }
        
        // Create container
        const container = document.createElement('div');
        container.className = isDisplayMath ? 'formula-container display-formula' : 'formula-container inline-formula';
        
        // Insert container before math element
        element.parentNode.insertBefore(container, element);
        
        // Move math element into container
        container.appendChild(element);
        
        // Add copy button
        addCopyButtonToFormula(container, element);
    });
}

/**
 * Add equation numbering to display equations
 */
function addEquationNumbering() {
    // Find all display math containers
    const displayEquations = document.querySelectorAll('.display-formula');
    
    let equationCounter = 1;
    
    displayEquations.forEach(container => {
        // Skip if already numbered
        if (container.querySelector('.equation-number')) {
            return;
        }
        
        // Create equation number element
        const numberElement = document.createElement('div');
        numberElement.className = 'equation-number';
        numberElement.textContent = `(${equationCounter})`;
        
        // Add number to container
        container.appendChild(numberElement);
        
        // Increment counter
        equationCounter++;
    });
}

/**
 * Add copy button to formula
 */
function addCopyButtonToFormula(container, formula) {
    // Skip if already has copy button
    if (container.querySelector('.formula-copy-btn')) {
        return;
    }
    
    // Create copy button
    const copyBtn = document.createElement('button');
    copyBtn.className = 'formula-copy-btn';
    copyBtn.setAttribute('aria-label', 'Copy formula');
    copyBtn.setAttribute('title', 'Copy formula');
    copyBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M4 1.5H3a2 2 0 0 0-2 2V14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V3.5a2 2 0 0 0-2-2h-1v1h1a1 1 0 0 1 1 1V14a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V3.5a1 1 0 0 1 1-1h1v-1z"/><path d="M9.5 1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5h3zm-3-1A1.5 1.5 0 0 0 5 1.5v1A1.5 1.5 0 0 0 6.5 4h3A1.5 1.5 0 0 0 11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3z"/></svg>';
    
    // Add click event
    copyBtn.addEventListener('click', function(e) {
        e.preventDefault();
        
        // Get formula text
        const formulaText = getFormulaText(formula);
        
        // Copy to clipboard
        navigator.clipboard.writeText(formulaText).then(() => {
            // Show success state
            copyBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg>';
            
            // Reset after 2 seconds
            setTimeout(() => {
                copyBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M4 1.5H3a2 2 0 0 0-2 2V14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V3.5a2 2 0 0 0-2-2h-1v1h1a1 1 0 0 1 1 1V14a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V3.5a1 1 0 0 1 1-1h1v-1z"/><path d="M9.5 1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5h3zm-3-1A1.5 1.5 0 0 0 5 1.5v1A1.5 1.5 0 0 0 6.5 4h3A1.5 1.5 0 0 0 11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3z"/></svg>';
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy formula:', err);
        });
    });
    
    // Add button to container
    container.appendChild(copyBtn);
}

/**
 * Get the LaTeX representation of a formula element
 */
function getFormulaText(formulaElement) {
    // Try to get source from data attribute first
    const source = formulaElement.getAttribute('data-source');
    if (source) {
        return source;
    }
    
    // Try to extract from MathJax v3 output
    const mjxContainer = formulaElement.querySelector('.MathJax');
    if (mjxContainer && mjxContainer.hasAttribute('data-latex')) {
        return mjxContainer.getAttribute('data-latex');
    }
    
    // For MathJax v2
    if (window.MathJax && window.MathJax.Hub) {
        const jax = window.MathJax.Hub.getAllJax(formulaElement);
        if (jax && jax.length > 0) {
            return jax[0].originalText;
        }
    }
    
    // Fallback to the element's text content
    return formulaElement.textContent;
}

/**
 * Add copy button to all formulas
 */
function addCopyButtonToFormulas() {
    const formulaContainers = document.querySelectorAll('.formula-container');
    
    formulaContainers.forEach(container => {
        const formula = container.querySelector('.math, .math-display');
        if (formula) {
            addCopyButtonToFormula(container, formula);
        }
    });
}

/**
 * Fix common formula rendering issues
 */
function fixFormulaRenderingIssues() {
    // Ensure MathJax is loaded and math is rendered
    if (window.MathJax) {
        if (window.MathJax.typesetPromise) {
            // MathJax v3
            window.MathJax.typesetPromise().catch(err => {
                console.error('MathJax typeset error:', err);
            });
        } else if (window.MathJax.Hub) {
            // MathJax v2
            window.MathJax.Hub.Queue(["Typeset", window.MathJax.Hub]);
        }
    }
    
    // Add observer for new content
    const observer = new MutationObserver(mutations => {
        let shouldRerender = false;
        
        mutations.forEach(mutation => {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                // Check if added nodes contain math
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === Node.ELEMENT_NODE && 
                        (node.querySelector('.math, .math-display') || 
                         node.classList.contains('math') || 
                         node.classList.contains('math-display'))) {
                        shouldRerender = true;
                    }
                });
            }
        });
        
        if (shouldRerender && window.MathJax) {
            if (window.MathJax.typesetPromise) {
                // MathJax v3
                window.MathJax.typesetPromise().catch(err => {
                    console.error('MathJax typeset error:', err);
                });
            } else if (window.MathJax.Hub) {
                // MathJax v2
                window.MathJax.Hub.Queue(["Typeset", window.MathJax.Hub]);
            }
        }
    });
    
    observer.observe(document.body, { childList: true, subtree: true });
} 