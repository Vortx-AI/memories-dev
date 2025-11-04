/**
 * Debug and fix rendering issues
 * This script identifies and fixes common rendering problems with Mermaid and MathJax
 */

(function() {
    // Log initialization
    console.log('Debug script initialized');
    
    // Track loaded resources
    const loadedResources = {
        mermaid: false,
        mathjax: false
    };
    
    // Check if resources are loaded
    function checkResources() {
        loadedResources.mermaid = (typeof window.mermaid !== 'undefined');
        loadedResources.mathjax = (typeof window.MathJax !== 'undefined');
        
        console.log('Resource status:', loadedResources);
        
        // Fix missing resources
        if (!loadedResources.mermaid) {
            loadMermaid();
        }
        
        if (!loadedResources.mathjax) {
            loadMathJax();
        }
    }
    
    // Load Mermaid if missing
    function loadMermaid() {
        console.log('Loading Mermaid library');
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/mermaid@9/dist/mermaid.min.js';
        script.onload = function() {
            console.log('Mermaid loaded successfully');
            loadedResources.mermaid = true;
            initializeMermaid();
        };
        script.onerror = function() {
            console.error('Failed to load Mermaid');
        };
        document.head.appendChild(script);
    }
    
    // Load MathJax if missing
    function loadMathJax() {
        console.log('Loading MathJax library');
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js';
        script.async = true;
        script.onload = function() {
            console.log('MathJax loaded successfully');
            loadedResources.mathjax = true;
        };
        script.onerror = function() {
            console.error('Failed to load MathJax');
        };
        document.head.appendChild(script);
    }
    
    // Initialize Mermaid with robust error handling
    function initializeMermaid() {
        if (typeof window.mermaid !== 'undefined') {
            try {
                console.log('Initializing Mermaid');
                window.mermaid.initialize({
                    startOnLoad: true,
                    theme: 'neutral',
                    securityLevel: 'loose',
                    flowchart: {
                        useMaxWidth: true,
                        htmlLabels: true,
                        curve: 'basis'
                    },
                    fontFamily: '"Palatino Linotype", "Book Antiqua", Palatino, serif'
                });
                
                // Force render all diagrams
                setTimeout(function() {
                    try {
                        console.log('Rendering Mermaid diagrams');
                        const diagrams = document.querySelectorAll('.mermaid:not([data-processed="true"])');
                        console.log(`Found ${diagrams.length} unprocessed diagrams`);
                        
                        if (diagrams.length > 0) {
                            window.mermaid.init(undefined, diagrams);
                        }
                    } catch (err) {
                        console.error('Error rendering Mermaid diagrams:', err);
                        fixBrokenDiagrams();
                    }
                }, 1000);
            } catch (err) {
                console.error('Error initializing Mermaid:', err);
                fixBrokenDiagrams();
            }
        }
    }
    
    // Fix broken diagrams by displaying their source
    function fixBrokenDiagrams() {
        console.log('Attempting to fix broken diagrams');
        document.querySelectorAll('.mermaid:not([data-processed="true"])').forEach(function(diagram) {
            const source = diagram.textContent.trim();
            const container = document.createElement('div');
            container.className = 'diagram-fallback';
            
            const header = document.createElement('div');
            header.className = 'diagram-fallback-header';
            header.textContent = 'Diagram Source:';
            
            const pre = document.createElement('pre');
            pre.textContent = source;
            
            container.appendChild(header);
            container.appendChild(pre);
            
            // Replace diagram with source
            diagram.innerHTML = '';
            diagram.appendChild(container);
            diagram.setAttribute('data-processed', 'fallback');
        });
    }
    
    // Fix whitespace issues
    function fixWhitespaceIssues() {
        console.log('Fixing whitespace issues');
        
        // Force content width
        const style = document.createElement('style');
        style.textContent = `
            .wy-nav-content {
                max-width: 1100px !important;
                margin: 0 auto !important;
                padding: 1.5em 2em !important;
            }
            
            @media screen and (min-width: 1400px) {
                .wy-nav-content {
                    max-width: 1200px !important;
                }
            }
            
            .wy-nav-content-wrap {
                margin-left: 300px !important;
            }
            
            .wy-nav-side {
                width: 300px !important;
            }
            
            @media screen and (max-width: 768px) {
                .wy-nav-content-wrap {
                    margin-left: 0 !important;
                }
                
                .wy-nav-side {
                    width: 85% !important;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Fix font loading issues
    function fixFontIssues() {
        console.log('Fixing font issues');
        
        // Ensure book fonts are loaded
        const fontLink = document.createElement('link');
        fontLink.rel = 'stylesheet';
        fontLink.href = 'https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,700;1,400;1,700&display=swap';
        document.head.appendChild(fontLink);
        
        // Apply book fonts with high specificity
        const style = document.createElement('style');
        style.textContent = `
            body, .wy-body-for-nav {
                font-family: 'Lora', 'Palatino Linotype', 'Book Antiqua', Palatino, serif !important;
            }
            
            h1, h2, h3, h4, h5, h6 {
                font-family: 'Lora', 'Palatino Linotype', 'Book Antiqua', Palatino, serif !important;
            }
            
            .wy-menu-vertical {
                font-family: 'Lora', 'Palatino Linotype', 'Book Antiqua', Palatino, serif !important;
            }
        `;
        document.head.appendChild(style);
    }
    
    // Apply all fixes when DOM is loaded
    document.addEventListener('DOMContentLoaded', function() {
        console.log('DOM loaded, applying fixes');
        checkResources();
        fixWhitespaceIssues();
        fixFontIssues();
        
        // Monitor for dynamic content changes
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                    // Check for new diagrams
                    if (loadedResources.mermaid) {
                        const newDiagrams = document.querySelectorAll('.mermaid:not([data-processed="true"]):not([data-processed="fallback"])');
                        if (newDiagrams.length > 0) {
                            console.log(`Found ${newDiagrams.length} new diagrams to render`);
                            try {
                                window.mermaid.init(undefined, newDiagrams);
                            } catch (err) {
                                console.error('Error rendering new diagrams:', err);
                                fixBrokenDiagrams();
                            }
                        }
                    }
                }
            });
        });
        
        observer.observe(document.body, { childList: true, subtree: true });
    });
    
    // Additional check after window load (for late resources)
    window.addEventListener('load', function() {
        console.log('Window loaded, checking resources again');
        checkResources();
        
        // Force render any remaining diagrams
        setTimeout(function() {
            if (loadedResources.mermaid) {
                const remainingDiagrams = document.querySelectorAll('.mermaid:not([data-processed="true"]):not([data-processed="fallback"])');
                if (remainingDiagrams.length > 0) {
                    console.log(`Found ${remainingDiagrams.length} remaining diagrams to render`);
                    try {
                        window.mermaid.init(undefined, remainingDiagrams);
                    } catch (err) {
                        console.error('Error rendering remaining diagrams:', err);
                        fixBrokenDiagrams();
                    }
                }
            }
        }, 2000);
    });
})(); 