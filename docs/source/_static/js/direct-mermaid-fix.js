/**
 * direct-mermaid-fix.js - Direct fix for Mermaid diagrams
 * 
 * This script ensures Mermaid diagrams are properly rendered by:
 * 1. Checking if Mermaid is available and loading it if not
 * 2. Initializing with optimal settings
 * 3. Explicitly rendering all diagrams found on the page
 * 4. Providing fallback rendering for failed diagrams
 * 5. Supporting dark/light mode themes
 */

(function() {
    // Wait for DOM to be fully loaded
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Direct Mermaid fix loaded');
        
        // Check if Mermaid is available
        if (typeof window.mermaid === 'undefined') {
            console.log('Mermaid not found, loading from CDN');
            loadMermaid();
        } else {
            console.log('Mermaid found, initializing');
            initMermaid();
        }
    });
    
    // Load Mermaid from CDN if not available
    function loadMermaid() {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/mermaid@9.4.3/dist/mermaid.min.js';
        script.onload = function() {
            console.log('Mermaid loaded from CDN');
            initMermaid();
        };
        script.onerror = function() {
            console.error('Failed to load Mermaid from CDN');
            // Try alternate CDN
            const altScript = document.createElement('script');
            altScript.src = 'https://unpkg.com/mermaid@9.4.3/dist/mermaid.min.js';
            altScript.onload = function() {
                console.log('Mermaid loaded from alternate CDN');
                initMermaid();
            };
            altScript.onerror = function() {
                console.error('Failed to load Mermaid from alternate CDN');
                createFallbackForAllDiagrams();
            };
            document.head.appendChild(altScript);
        };
        document.head.appendChild(script);
    }
    
    // Initialize Mermaid with optimal settings
    function initMermaid() {
        try {
            // Configure Mermaid
            window.mermaid.initialize({
                startOnLoad: false,  // We'll manually render
                theme: isDarkMode() ? 'dark' : 'default',
                securityLevel: 'loose',
                flowchart: {
                    useMaxWidth: false,
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
                themeVariables: {
                    primaryColor: isDarkMode() ? '#5D8AA8' : '#5D8AA8',
                    primaryTextColor: isDarkMode() ? '#fff' : '#fff',
                    primaryBorderColor: isDarkMode() ? '#5D8AA8' : '#5D8AA8',
                    lineColor: isDarkMode() ? '#5D8AA8' : '#5D8AA8',
                    secondaryColor: isDarkMode() ? '#006100' : '#006100',
                    tertiaryColor: isDarkMode() ? '#333' : '#fff'
                }
            });
            
            // Find all Mermaid diagrams
            renderAllDiagrams();
            
            // Add a mutation observer to catch dynamically added diagrams
            observeDOMChanges();
            
            // Listen for theme changes
            listenForThemeChanges();
            
        } catch (err) {
            console.error('Error initializing Mermaid:', err);
            createFallbackForAllDiagrams();
        }
    }
    
    // Check if dark mode is enabled
    function isDarkMode() {
        return document.documentElement.classList.contains('dark-theme') || 
               document.body.classList.contains('dark-theme') ||
               window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    
    // Listen for theme changes
    function listenForThemeChanges() {
        // Listen for class changes on html or body elements
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.attributeName === 'class') {
                    // Reinitialize mermaid with new theme
                    window.mermaid.initialize({
                        theme: isDarkMode() ? 'dark' : 'default',
                        themeVariables: {
                            primaryColor: isDarkMode() ? '#5D8AA8' : '#5D8AA8',
                            primaryTextColor: isDarkMode() ? '#fff' : '#fff',
                            primaryBorderColor: isDarkMode() ? '#5D8AA8' : '#5D8AA8',
                            lineColor: isDarkMode() ? '#5D8AA8' : '#5D8AA8',
                            secondaryColor: isDarkMode() ? '#006100' : '#006100',
                            tertiaryColor: isDarkMode() ? '#333' : '#fff'
                        }
                    });
                    
                    // Re-render all diagrams
                    renderAllDiagrams(true);
                }
            });
        });
        
        observer.observe(document.documentElement, { attributes: true });
        observer.observe(document.body, { attributes: true });
        
        // Listen for system preference changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function() {
            window.mermaid.initialize({
                theme: isDarkMode() ? 'dark' : 'default'
            });
            renderAllDiagrams(true);
        });
    }
    
    // Render all diagrams on the page
    function renderAllDiagrams(forceRerender = false) {
        try {
            // Find all Mermaid diagrams (both div.mermaid and pre.mermaid)
            const diagrams = document.querySelectorAll('.mermaid, div.mermaid, pre.mermaid');
            console.log(`Found ${diagrams.length} Mermaid diagrams`);
            
            if (diagrams.length === 0) {
                return;
            }
            
            // Process each diagram
            diagrams.forEach(function(diagram, index) {
                // Skip already processed diagrams unless force rerender
                if (diagram.getAttribute('data-processed') === 'true' && !forceRerender) {
                    console.log(`Diagram ${index} already processed`);
                    return;
                }
                
                try {
                    // Get diagram content
                    const content = diagram.textContent.trim();
                    if (!content) {
                        console.log(`Diagram ${index} has no content`);
                        return;
                    }
                    
                    console.log(`Processing diagram ${index}: ${content.substring(0, 50)}...`);
                    
                    // Create a unique ID for the diagram
                    const id = `mermaid-diagram-${index}-${Date.now()}`;
                    diagram.id = id;
                    
                    // If force rerendering, we need to clear the diagram first
                    if (forceRerender) {
                        diagram.innerHTML = content;
                        diagram.removeAttribute('data-processed');
                    }
                    
                    // Render the diagram
                    window.mermaid.render(id, content, function(svgCode) {
                        diagram.innerHTML = svgCode;
                        diagram.setAttribute('data-processed', 'true');
                        console.log(`Diagram ${index} rendered successfully`);
                        
                        // Make diagram clickable to expand
                        makeExpandable(diagram);
                    }, diagram);
                } catch (err) {
                    console.error(`Error rendering diagram ${index}:`, err);
                    createFallback(diagram, diagram.textContent, err);
                }
            });
        } catch (err) {
            console.error('Error rendering diagrams:', err);
            createFallbackForAllDiagrams();
        }
    }
    
    // Make diagram expandable on click
    function makeExpandable(diagram) {
        // Add click handler
        diagram.style.cursor = 'pointer';
        diagram.addEventListener('click', function(e) {
            // Prevent click from propagating
            e.stopPropagation();
            
            if (this.classList.contains('expanded')) {
                // Close expanded view
                this.classList.remove('expanded');
                document.body.classList.remove('has-expanded-diagram');
            } else {
                // Open expanded view
                this.classList.add('expanded');
                document.body.classList.add('has-expanded-diagram');
                
                // Close when clicking outside
                const closeOnClickOutside = function(event) {
                    if (!diagram.contains(event.target)) {
                        diagram.classList.remove('expanded');
                        document.body.classList.remove('has-expanded-diagram');
                        document.removeEventListener('click', closeOnClickOutside);
                    }
                };
                
                setTimeout(function() {
                    document.addEventListener('click', closeOnClickOutside);
                }, 100);
            }
        });
    }
    
    // Create fallback for failed diagrams
    function createFallback(diagram, content, error) {
        const fallback = document.createElement('div');
        fallback.className = 'diagram-fallback';
        
        const header = document.createElement('div');
        header.className = 'diagram-fallback-header';
        header.textContent = 'Diagram Source (Failed to Render):';
        
        const errorMsg = document.createElement('div');
        errorMsg.className = 'diagram-fallback-error';
        errorMsg.textContent = `Error: ${error.message || 'Unknown error'}`;
        
        const pre = document.createElement('pre');
        pre.textContent = content;
        
        fallback.appendChild(header);
        fallback.appendChild(errorMsg);
        fallback.appendChild(pre);
        
        // Replace the diagram with the fallback
        diagram.parentNode.replaceChild(fallback, diagram);
    }
    
    // Create fallbacks for all diagrams
    function createFallbackForAllDiagrams() {
        const diagrams = document.querySelectorAll('.mermaid:not([data-processed="true"])');
        diagrams.forEach(function(diagram) {
            createFallback(diagram, diagram.textContent, { message: 'Mermaid initialization failed' });
        });
    }
    
    // Observe DOM changes to catch dynamically added diagrams
    function observeDOMChanges() {
        // Create an observer instance
        const observer = new MutationObserver(function(mutations) {
            let shouldRender = false;
            
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    // Check if any added nodes contain mermaid diagrams
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1) { // Element node
                            if (node.classList && node.classList.contains('mermaid')) {
                                shouldRender = true;
                            } else if (node.querySelector && node.querySelector('.mermaid')) {
                                shouldRender = true;
                            }
                        }
                    });
                }
            });
            
            if (shouldRender) {
                console.log('New diagrams detected, rendering...');
                setTimeout(renderAllDiagrams, 100); // Small delay to ensure DOM is updated
            }
        });
        
        // Start observing the document with the configured parameters
        observer.observe(document.body, { childList: true, subtree: true });
    }
    
    // Add CSS for fallbacks and expanded diagrams
    function addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .diagram-fallback {
                border: 1px solid #e1e1e1;
                border-radius: 5px;
                padding: 1em;
                margin: 2em 0;
                background-color: #f8f8f8;
                overflow-x: auto;
            }
            
            .diagram-fallback-header {
                font-weight: bold;
                margin-bottom: 0.5em;
                color: #666;
            }
            
            .diagram-fallback-error {
                color: #c00;
                margin-bottom: 1em;
                font-style: italic;
            }
            
            .diagram-fallback pre {
                margin: 0;
                white-space: pre-wrap;
                font-size: 0.9em;
                background-color: transparent;
                border: none;
                padding: 0;
            }
            
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
            
            .dark-theme .mermaid.expanded {
                background: #2d3748;
                box-shadow: 0 0 20px rgba(0,0,0,0.8);
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
                color: #666;
                font-size: 0.9em;
            }
            
            .dark-theme .mermaid.expanded::after {
                color: #ccc;
            }
            
            body.has-expanded-diagram {
                overflow: hidden;
            }
            
            @media print {
                .mermaid.expanded {
                    position: static;
                    transform: none;
                    box-shadow: none;
                    max-width: 100%;
                    max-height: none;
                    break-inside: avoid;
                }
                
                .mermaid.expanded::after {
                    display: none;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Add styles
    addStyles();
    
    // Add global function that can be called manually if needed
    window.renderAllMermaidDiagrams = renderAllDiagrams;
})(); 