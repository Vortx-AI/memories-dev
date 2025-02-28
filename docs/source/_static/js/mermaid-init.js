document.addEventListener('DOMContentLoaded', function() {
    // Initialize Mermaid with default settings
    mermaid.initialize({
        startOnLoad: true,
        theme: 'default', // Default light theme
        flowchart: {
            useMaxWidth: true,
            htmlLabels: true,
            curve: 'basis'
        },
        securityLevel: 'loose',
        fontFamily: 'Crimson Pro, serif'
    });
    
    // Update Mermaid theme based on current color scheme
    function updateMermaidTheme() {
        const isDarkMode = document.documentElement.classList.contains('dark-theme');
        
        // Get all Mermaid diagrams
        const diagrams = document.querySelectorAll('.mermaid');
        
        // Set theme based on current mode
        mermaid.initialize({
            theme: isDarkMode ? 'dark' : 'default'
        });
        
        // Force redraw diagrams with new theme
        if (diagrams.length > 0) {
            diagrams.forEach(diagram => {
                const content = diagram.textContent;
                diagram.textContent = '';
                diagram.textContent = content;
            });
            mermaid.init(undefined, '.mermaid');
        }
    }
    
    // Initial theme setup - default to light theme
    updateMermaidTheme();
    
    // Listen for theme toggle events
    document.addEventListener('themeToggled', updateMermaidTheme);
    
    // Remove system preference check to ensure default is light
    // window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', updateMermaidTheme);
}); 