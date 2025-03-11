/**
 * Mermaid initialization for Memories-Dev Documentation
 */
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
                window.mermaid.init(undefined, document.querySelectorAll('.mermaid'));
            } catch (err) {
                console.error('Error initializing mermaid:', err);
                document.querySelectorAll('.mermaid').forEach(function(diagram) {
                    if (!diagram.getAttribute('data-processed')) {
                        diagram.innerHTML = '<div class="mermaid-error">Error rendering diagram</div>';
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
}); 