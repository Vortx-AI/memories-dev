/**
 * Simplified Mermaid initialization for ReadTheDocs
 * Optimized for Mermaid 10.6.1 compatibility
 */
(function() {
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Initializing Mermaid 10.6.1 for ReadTheDocs');
        
        function initMermaid() {
            if (typeof window.mermaid !== 'undefined') {
                try {
                    window.mermaid.initialize({
                        startOnLoad: false,
                        theme: 'neutral',
                        securityLevel: 'loose',
                        flowchart: {
                            useMaxWidth: true,
                            htmlLabels: true,
                            curve: 'basis'
                        }
                    });
                    
                    var diagrams = document.querySelectorAll('.mermaid:not([data-processed="true"])');
                    console.log('Found ' + diagrams.length + ' diagrams to process');
                    
                    if (diagrams.length > 0) {
                        window.mermaid.run({
                            nodes: Array.from(diagrams)
                        }).catch(function(err) {
                            console.error('Mermaid run error:', err);
                        });
                    }
                } catch (err) {
                    console.error('Mermaid initialization error:', err);
                }
            } else {
                // Retry after a delay
                setTimeout(initMermaid, 500);
            }
        }
        
        // Try to initialize after a short delay
        setTimeout(initMermaid, 100);
        
        // Also try again after page is fully loaded
        window.addEventListener('load', function() {
            setTimeout(initMermaid, 500);
        });
    });
})(); 