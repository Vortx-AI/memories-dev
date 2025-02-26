// Formula Enhancer for memories-dev documentation
document.addEventListener('DOMContentLoaded', function() {
    // Initialize formula enhancer
    initializeFormulaEnhancer();
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
}

/**
 * Configure MathJax for better formula rendering
 */
function configureMathJax() {
    if (window.MathJax) {
        // For MathJax v3
        if (window.MathJax.version && window.MathJax.version[0] === '3') {
            window.MathJax.startup = window.MathJax.startup || {};
            window.MathJax.startup.ready = () => {
                window.MathJax.startup.defaultReady();
                enhanceFormulaDisplay();
            };
        } 
        // For MathJax v2
        else if (window.MathJax.Hub) {
            window.MathJax.Hub.Register.StartupHook('End', function() {
                enhanceFormulaDisplay();
            });
        }
    } else {
        // If MathJax is not loaded yet, wait for it
        const checkMathJax = setInterval(function() {
            if (window.MathJax) {
                clearInterval(checkMathJax);
                configureMathJax();
            }
        }, 500);
        
        // Stop checking after 10 seconds
        setTimeout(function() {
            clearInterval(checkMathJax);
        }, 10000);
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
            background-color: var(--primary-light, #f8f9fa);
            border-radius: 4px;
            border-left: 3px solid var(--accent-color, #4285f4);
        }
        
        /* Inline formula */
        .math {
            font-family: 'STIXGeneral', 'Georgia', 'Times', serif;
        }
        
        /* Display formula */
        .math-display {
            display: block;
            overflow-x: auto;
            overflow-y: hidden;
            padding: 0.5rem 0;
        }
        
        /* Formula number */
        .formula-number {
            position: absolute;
            right: 1rem;
            top: 50%;
            transform: translateY(-50%);
            font-size: 0.9rem;
            color: var(--text-muted, #5f6368);
            user-select: none;
        }
        
        /* Formula copy button */
        .formula-copy {
            position: absolute;
            top: 0.5rem;
            right: 0.5rem;
            background-color: transparent;
            border: none;
            color: var(--text-muted, #5f6368);
            cursor: pointer;
            padding: 0.25rem;
            border-radius: 3px;
            opacity: 0;
            transition: opacity 0.2s ease, background-color 0.2s ease;
        }
        
        .formula-container:hover .formula-copy {
            opacity: 0.7;
        }
        
        .formula-copy:hover {
            opacity: 1 !important;
            background-color: rgba(0, 0, 0, 0.05);
        }
        
        .formula-copy svg {
            width: 16px;
            height: 16px;
        }
        
        /* Formula tooltip */
        .formula-tooltip {
            position: absolute;
            top: -2rem;
            right: 0.5rem;
            background-color: var(--text-color, #202124);
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 3px;
            font-size: 0.8rem;
            opacity: 0;
            transition: opacity 0.2s ease;
            pointer-events: none;
        }
        
        .formula-tooltip.visible {
            opacity: 0.9;
        }
        
        /* Formula label */
        .formula-label {
            font-size: 0.8rem;
            color: var(--text-muted, #5f6368);
            margin-top: 0.25rem;
            text-align: right;
        }
        
        /* MathJax specific styles */
        .MathJax_Display {
            margin: 0 !important;
        }
        
        .MathJax {
            outline: none;
        }
        
        /* Responsive styles */
        @media (max-width: 768px) {
            .formula-container {
                padding: 0.75rem;
                margin: 1rem 0;
            }
            
            .formula-number {
                font-size: 0.8rem;
            }
            
            .formula-copy {
                opacity: 0.7;
            }
        }
    `;
    
    document.head.appendChild(style);
}

/**
 * Enhance formula display
 */
function enhanceFormulaDisplay() {
    // Process all display math elements
    const displayMath = document.querySelectorAll('.math-display, .MathJax_Display');
    
    displayMath.forEach((element, index) => {
        // Skip elements that are already enhanced
        if (element.parentElement.classList.contains('formula-container')) {
            return;
        }
        
        // Create formula container
        const container = document.createElement('div');
        container.className = 'formula-container';
        container.setAttribute('role', 'math');
        container.setAttribute('aria-label', 'Mathematical formula');
        
        // Add formula number
        const formulaNumber = document.createElement('div');
        formulaNumber.className = 'formula-number';
        formulaNumber.textContent = `(${index + 1})`;
        
        // Wrap formula in container
        element.parentNode.insertBefore(container, element);
        container.appendChild(element);
        container.appendChild(formulaNumber);
        
        // Add copy button
        addCopyButtonToFormula(container, element);
    });
    
    // Process all inline math elements
    const inlineMath = document.querySelectorAll('.math:not(.math-display), .MathJax:not(.MathJax_Display)');
    
    inlineMath.forEach(element => {
        // Skip elements that are already enhanced
        if (element.classList.contains('enhanced')) {
            return;
        }
        
        // Add enhanced class
        element.classList.add('enhanced');
        
        // Add title attribute for hover preview
        if (element.textContent) {
            element.setAttribute('title', element.textContent);
        }
    });
}

/**
 * Add copy button to formula
 * @param {HTMLElement} container - The formula container
 * @param {HTMLElement} formula - The formula element
 */
function addCopyButtonToFormula(container, formula) {
    // Create copy button
    const copyButton = document.createElement('button');
    copyButton.className = 'formula-copy';
    copyButton.setAttribute('aria-label', 'Copy formula');
    copyButton.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
    `;
    
    // Create tooltip
    const tooltip = document.createElement('div');
    tooltip.className = 'formula-tooltip';
    tooltip.textContent = 'Copied!';
    
    // Add copy button and tooltip to container
    container.appendChild(copyButton);
    container.appendChild(tooltip);
    
    // Add event listener to copy button
    copyButton.addEventListener('click', function() {
        // Get formula text
        let formulaText = '';
        
        // Try to get LaTeX source
        if (formula.tagName === 'SCRIPT' && formula.type === 'math/tex') {
            formulaText = formula.textContent;
        } else if (formula.classList.contains('MathJax') || formula.classList.contains('MathJax_Display')) {
            // For MathJax v3
            if (window.MathJax && window.MathJax.version && window.MathJax.version[0] === '3') {
                const mjxContainer = formula.closest('.MathJax');
                if (mjxContainer && mjxContainer.dataset.mathml) {
                    formulaText = mjxContainer.dataset.mathml;
                }
            } 
            // For MathJax v2
            else if (window.MathJax && window.MathJax.Hub) {
                const jax = window.MathJax.Hub.getAllJax(formula);
                if (jax && jax.length > 0) {
                    formulaText = jax[0].originalText;
                }
            }
        } else {
            // Fallback to element text
            formulaText = formula.textContent;
        }
        
        // Copy to clipboard
        if (formulaText) {
            navigator.clipboard.writeText(formulaText).then(function() {
                // Show tooltip
                tooltip.classList.add('visible');
                
                // Hide tooltip after 2 seconds
                setTimeout(function() {
                    tooltip.classList.remove('visible');
                }, 2000);
            }).catch(function(err) {
                console.error('Could not copy formula: ', err);
            });
        }
    });
}

/**
 * Add copy button to all formulas
 */
function addCopyButtonToFormulas() {
    // Process all formula containers that don't have copy buttons
    const containers = document.querySelectorAll('.formula-container:not(:has(.formula-copy))');
    
    containers.forEach(container => {
        const formula = container.querySelector('.math-display, .MathJax_Display');
        if (formula) {
            addCopyButtonToFormula(container, formula);
        }
    });
}

/**
 * Fix formula rendering issues
 */
function fixFormulaRenderingIssues() {
    // Fix overflow issues
    const mathElements = document.querySelectorAll('.MathJax_Display, .math-display');
    mathElements.forEach(element => {
        element.style.overflowX = 'auto';
        element.style.overflowY = 'hidden';
    });
    
    // Fix alignment issues
    const alignedMath = document.querySelectorAll('.align, .align\\*');
    alignedMath.forEach(element => {
        element.style.display = 'block';
        element.style.width = '100%';
    });
    
    // Fix equation numbering
    const equations = document.querySelectorAll('.equation');
    equations.forEach((equation, index) => {
        const number = equation.querySelector('.eqno');
        if (number) {
            number.textContent = `(${index + 1})`;
        }
    });
    
    // Add observer for dynamically loaded content
    const observer = new MutationObserver(function(mutations) {
        let mathAdded = false;
        
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        const mathElements = node.querySelectorAll('.math, .MathJax');
                        if (mathElements.length) {
                            mathAdded = true;
                        }
                    }
                });
            }
        });
        
        if (mathAdded) {
            // Re-run enhanceFormulaDisplay after a short delay
            setTimeout(enhanceFormulaDisplay, 500);
        }
    });
    
    observer.observe(document.body, { childList: true, subtree: true });
} 