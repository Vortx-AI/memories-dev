/**
 * diagram-math-fix.js - Fixes for Mermaid diagrams and MathJax rendering
 * 
 * This script provides robust initialization and error handling for
 * Mermaid diagrams and MathJax math rendering in the documentation.
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing diagram and math rendering fixes');
    
    // Initialize Mermaid with proper configuration
    initializeMermaid();
    
    // Initialize MathJax with proper configuration
    initializeMathJax();
    
    // Add window load event to catch any diagrams that might be added dynamically
    window.addEventListener('load', function() {
        setTimeout(function() {
            renderAllDiagrams();
            renderAllMathElements();
        }, 1000);
    });
});

/**
 * Initialize Mermaid library with proper configuration
 */
function initializeMermaid() {
    if (typeof window.mermaid !== 'undefined') {
        try {
            console.log('Configuring Mermaid');
            window.mermaid.initialize({
                startOnLoad: true,
                theme: 'neutral',
                securityLevel: 'loose',
                flowchart: {
                    useMaxWidth: true,
                    htmlLabels: true,
                    curve: 'basis'
                },
                sequence: {
                    diagramMarginX: 50,
                    diagramMarginY: 10,
                    actorMargin: 50,
                    width: 150,
                    height: 65
                },
                gantt: {
                    titleTopMargin: 25,
                    barHeight: 20,
                    barGap: 4,
                    topPadding: 50,
                    leftPadding: 75
                },
                fontFamily: '"Lora", "Palatino Linotype", "Book Antiqua", Palatino, serif'
            });
            
            // Force render all diagrams
            setTimeout(renderAllDiagrams, 500);
        } catch (err) {
            console.error('Error initializing Mermaid:', err);
            loadMermaidFallback();
        }
    } else {
        console.warn('Mermaid library not found, loading from CDN');
        loadMermaidFallback();
    }
}

/**
 * Load Mermaid from CDN if not available
 */
function loadMermaidFallback() {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/mermaid@9.4.3/dist/mermaid.min.js';
    script.integrity = 'sha256-e0o3JYsdjqKajf9eOe22FhioYSz9WofRY4dLKo3F6do=';
    script.crossOrigin = 'anonymous';
    script.onload = function() {
        console.log('Mermaid loaded successfully from CDN');
        initializeMermaid();
    };
    script.onerror = function() {
        console.error('Failed to load Mermaid from CDN');
        createFallbackDiagrams();
    };
    document.head.appendChild(script);
}

/**
 * Render all Mermaid diagrams on the page
 */
function renderAllDiagrams() {
    try {
        console.log('Rendering all Mermaid diagrams');
        const diagrams = document.querySelectorAll('.mermaid:not([data-processed="true"])');
        console.log(`Found ${diagrams.length} unprocessed diagrams`);
        
        if (diagrams.length > 0 && typeof window.mermaid !== 'undefined') {
            window.mermaid.init(undefined, diagrams);
            
            // Add click handler to make diagrams expandable
            document.querySelectorAll('.mermaid[data-processed="true"]').forEach(function(diagram) {
                diagram.style.cursor = 'pointer';
                diagram.addEventListener('click', function() {
                    if (this.classList.contains('expanded')) {
                        this.classList.remove('expanded');
                    } else {
                        this.classList.add('expanded');
                    }
                });
            });
        }
    } catch (err) {
        console.error('Error rendering Mermaid diagrams:', err);
        createFallbackDiagrams();
    }
}

/**
 * Create fallback representations for diagrams that failed to render
 */
function createFallbackDiagrams() {
    console.log('Creating fallback representations for diagrams');
    const diagrams = document.querySelectorAll('.mermaid:not([data-processed="true"])');
    
    diagrams.forEach(function(diagram) {
        const code = diagram.textContent.trim();
        const fallback = document.createElement('div');
        fallback.className = 'diagram-fallback';
        
        const header = document.createElement('div');
        header.className = 'diagram-fallback-header';
        header.textContent = 'Diagram Source:';
        
        const pre = document.createElement('pre');
        pre.textContent = code;
        
        fallback.appendChild(header);
        fallback.appendChild(pre);
        
        // Replace the diagram with the fallback
        diagram.parentNode.replaceChild(fallback, diagram);
    });
}

/**
 * Initialize MathJax with proper configuration
 */
function initializeMathJax() {
    if (typeof window.MathJax !== 'undefined') {
        try {
            console.log('Configuring MathJax');
            window.MathJax = {
                tex: {
                    inlineMath: [['\\(', '\\)']],
                    displayMath: [['\\[', '\\]'], ['$$', '$$']],
                    processEscapes: true,
                    processEnvironments: true,
                    processRefs: true
                },
                options: {
                    ignoreHtmlClass: 'tex2jax_ignore',
                    processHtmlClass: 'tex2jax_process'
                },
                startup: {
                    ready: function() {
                        console.log('MathJax is loaded and ready');
                        MathJax.startup.defaultReady();
                    }
                },
                chtml: {
                    scale: 1.1
                }
            };
            
            // Force render all math elements
            setTimeout(renderAllMathElements, 500);
        } catch (err) {
            console.error('Error initializing MathJax:', err);
            loadMathJaxFallback();
        }
    } else {
        console.warn('MathJax library not found, loading from CDN');
        loadMathJaxFallback();
    }
}

/**
 * Load MathJax from CDN if not available
 */
function loadMathJaxFallback() {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js';
    script.async = true;
    script.onload = function() {
        console.log('MathJax loaded successfully from CDN');
        renderAllMathElements();
    };
    script.onerror = function() {
        console.error('Failed to load MathJax from CDN');
    };
    document.head.appendChild(script);
}

/**
 * Render all math elements on the page
 */
function renderAllMathElements() {
    if (typeof window.MathJax !== 'undefined' && typeof window.MathJax.typeset === 'function') {
        try {
            console.log('Rendering all math elements');
            window.MathJax.typeset();
        } catch (err) {
            console.error('Error rendering math elements:', err);
        }
    }
}

// Add CSS for expanded diagrams
(function() {
    const style = document.createElement('style');
    style.textContent = `
        .mermaid.expanded {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 1000;
            background: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 0 20px rgba(0,0,0,0.5);
            max-width: 90vw;
            max-height: 90vh;
            overflow: auto;
        }
        
        .mermaid.expanded svg {
            max-width: 100% !important;
            max-height: 80vh !important;
            width: auto !important;
            height: auto !important;
        }
        
        .mermaid.expanded::after {
            content: "Click to close";
            display: block;
            text-align: center;
            margin-top: 10px;
            font-size: 12px;
            color: #666;
        }
        
        .mermaid:not(.expanded)::after {
            content: "Click to enlarge";
            display: block;
            text-align: center;
            margin-top: 5px;
            font-size: 10px;
            color: #999;
            opacity: 0;
            transition: opacity 0.3s;
        }
        
        .mermaid:not(.expanded):hover::after {
            opacity: 1;
        }
    `;
    document.head.appendChild(style);
})(); 