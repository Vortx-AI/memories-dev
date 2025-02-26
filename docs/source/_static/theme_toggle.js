// Theme toggle for documentation
document.addEventListener('DOMContentLoaded', function() {
    // Create the theme toggle button
    createThemeToggle();
    
    // Initialize the theme based on user preference or system settings
    initializeTheme();
});

/**
 * Create the theme toggle button
 */
function createThemeToggle() {
    // Create container
    const container = document.createElement('div');
    container.className = 'theme-toggle-container';
    
    // Create button
    const btn = document.createElement('button');
    btn.className = 'theme-toggle-button';
    btn.setAttribute('aria-label', 'Toggle dark/light mode');
    btn.setAttribute('title', 'Toggle dark/light mode');
    
    // Set initial icon based on current theme
    const isDarkTheme = document.documentElement.classList.contains('dark-theme');
    btn.innerHTML = isDarkTheme ? '☀️' : '🌙';
    
    // Add click event
    btn.addEventListener('click', toggleTheme);
    
    // Add button to container
    container.appendChild(btn);
    
    // Add to page - try multiple possible parent elements
    const searchBox = document.querySelector('.wy-side-nav-search');
    const navTop = document.querySelector('.wy-nav-top');
    
    if (searchBox) {
        searchBox.appendChild(container);
    } else if (navTop) {
        navTop.appendChild(container);
    } else {
        // Fallback to body if neither element exists
        document.body.appendChild(container);
    }
}

/**
 * Toggle between light and dark themes
 */
function toggleTheme() {
    // Get theme toggle button
    const btn = document.querySelector('.theme-toggle-button');
    if (!btn) return;
    
    // Toggle dark-theme class on html element
    document.documentElement.classList.toggle('dark-theme');
    
    // Update button icon
    const isDarkTheme = document.documentElement.classList.contains('dark-theme');
    btn.innerHTML = isDarkTheme ? '☀️' : '🌙';
    
    // Save preference to localStorage
    localStorage.setItem('theme', isDarkTheme ? 'dark' : 'light');
    
    // Update mermaid diagrams if they exist
    updateMermaidTheme(isDarkTheme);
    
    // Dispatch event for other components to react to theme change
    document.dispatchEvent(new CustomEvent('themeChanged', { 
        detail: { theme: isDarkTheme ? 'dark' : 'light' } 
    }));
}

/**
 * Initialize theme based on saved preference or system preference
 */
function initializeTheme() {
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme');
    
    if (savedTheme) {
        // Apply saved theme
        if (savedTheme === 'dark') {
            document.documentElement.classList.add('dark-theme');
        } else {
            document.documentElement.classList.remove('dark-theme');
        }
    } else {
        // Check system preference
        const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
        
        if (prefersDarkScheme.matches) {
            document.documentElement.classList.add('dark-theme');
        } else {
            document.documentElement.classList.remove('dark-theme');
        }
        
        // Listen for system preference changes
        prefersDarkScheme.addEventListener('change', function(e) {
            if (e.matches) {
                document.documentElement.classList.add('dark-theme');
            } else {
                document.documentElement.classList.remove('dark-theme');
            }
            
            // Update button if it exists
            const btn = document.querySelector('.theme-toggle-button');
            if (btn) {
                const isDarkTheme = document.documentElement.classList.contains('dark-theme');
                btn.innerHTML = isDarkTheme ? '☀️' : '🌙';
            }
        });
    }
    
    // Update button if it exists
    const btn = document.querySelector('.theme-toggle-button');
    if (btn) {
        const isDarkTheme = document.documentElement.classList.contains('dark-theme');
        btn.innerHTML = isDarkTheme ? '☀️' : '🌙';
    }
}

/**
 * Update Mermaid diagrams theme when theme is changed
 */
function updateMermaidTheme(isDarkTheme) {
    if (window.mermaid) {
        try {
            window.mermaid.initialize({
                theme: isDarkTheme ? 'dark' : 'default'
            });
            
            // Find all mermaid diagrams
            document.querySelectorAll('.mermaid').forEach(function(diagram) {
                // Get the original mermaid code
                const code = diagram.getAttribute('data-source') || diagram.textContent;
                if (!code) return;
                
                // Store original source if not already stored
                if (!diagram.getAttribute('data-source')) {
                    diagram.setAttribute('data-source', code);
                }
                
                // Clear the current diagram
                diagram.innerHTML = '';
                
                // Re-render with new theme
                window.mermaid.render('mermaid-svg-' + Math.random().toString(36).substr(2, 9), code, function(svgCode) {
                    diagram.innerHTML = svgCode;
                });
            });
        } catch (e) {
            console.error('Error updating mermaid diagrams:', e);
        }
    }
} 