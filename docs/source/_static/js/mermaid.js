/**
 * Mermaid initialization for Memories-Dev Documentation
 */
(function() {
    // Wait for DOM to be fully loaded
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Initializing Mermaid');
        
        // Initialize Mermaid with a timeout to ensure it's loaded
        function initMermaid() {
            if (typeof window.mermaid !== 'undefined') {
                try {
                    console.log('Configuring Mermaid');
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
                    
                    console.log('Rendering Mermaid diagrams');
                    var diagrams = document.querySelectorAll('.mermaid');
                    console.log('Found ' + diagrams.length + ' diagrams');
                    
                    if (diagrams.length > 0) {
                        window.mermaid.init(undefined, diagrams);
                    }
                } catch (err) {
                    console.error('Error initializing mermaid:', err);
                    document.querySelectorAll('.mermaid').forEach(function(diagram) {
                        if (!diagram.getAttribute('data-processed')) {
                            diagram.innerHTML = '<div class="mermaid-error">Error rendering diagram: ' + err.message + '</div>';
                        }
                    });
                }
            } else {
                console.log('Mermaid not loaded yet, retrying in 500ms');
                setTimeout(initMermaid, 500);
            }
        }
        
        // Try to initialize immediately
        initMermaid();
        
        // Also try again after a delay to ensure everything is loaded
        setTimeout(initMermaid, 1000);
        
        // And once more after page is fully loaded
        window.addEventListener('load', function() {
            setTimeout(initMermaid, 500);
        });
        
        // Add a final attempt after 3 seconds
        setTimeout(initMermaid, 3000);
    });
})(); 