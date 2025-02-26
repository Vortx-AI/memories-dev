// Theme toggle for documentation
document.addEventListener('DOMContentLoaded', function() {
    // Create the theme toggle styles
    addThemeStyles();
    
    // Create the theme toggle button
    createThemeToggle();
    
    // Initialize the theme based on user preference or system settings
    initializeTheme();
});

/**
 * Add the CSS styles for light and dark themes
 */
function addThemeStyles() {
    const styleEl = document.createElement('style');
    styleEl.id = 'theme-styles';
    styleEl.textContent = `
        /* Light theme variables (default) */
        :root {
            --bg-color: #ffffff;
            --bg-secondary-color: #f8f9fa;
            --bg-tertiary-color: #f0f1f2;
            --text-color: #222222;
            --text-muted: #6c757d;
            --link-color: #0866c6;
            --link-hover-color: #065096;
            --border-color: #e1e4e8;
            --shadow-color: rgba(0, 0, 0, 0.1);
            --code-bg: #f6f8fa;
            --code-color: #24292e;
            --table-header-bg: #f1f3f4;
            --table-border-color: #e0e0e0;
            --admonition-bg: rgba(240, 240, 240, 0.3);
            --admonition-success-bg: rgba(46, 204, 113, 0.1);
            --admonition-warning-bg: rgba(243, 156, 18, 0.1);
            --admonition-note-bg: rgba(41, 128, 185, 0.1);
            --admonition-caution-bg: rgba(231, 76, 60, 0.1);
            --transition: background-color 0.3s ease, color 0.3s ease;
        }
        
        /* Dark theme variables */
        [data-theme="dark"] {
            --bg-color: #1a1a1a;
            --bg-secondary-color: #2d2d2d;
            --bg-tertiary-color: #383838;
            --text-color: #e0e0e0;
            --text-muted: #a0a0a0;
            --link-color: #58a6ff;
            --link-hover-color: #79bcff;
            --border-color: #4d4d4d;
            --shadow-color: rgba(0, 0, 0, 0.5);
            --code-bg: #2b2b2b;
            --code-color: #e6e6e6;
            --table-header-bg: #3a3a3a;
            --table-border-color: #4d4d4d;
            --admonition-bg: rgba(50, 50, 50, 0.3);
            --admonition-success-bg: rgba(46, 204, 113, 0.15);
            --admonition-warning-bg: rgba(243, 156, 18, 0.15);
            --admonition-note-bg: rgba(41, 128, 185, 0.15);
            --admonition-caution-bg: rgba(231, 76, 60, 0.15);
        }
        
        /* Apply theme variables to elements */
        body, .wy-nav-content {
            background-color: var(--bg-color) !important;
            color: var(--text-color) !important;
            transition: var(--transition);
        }
        
        .wy-nav-side, .wy-side-nav-search, .wy-menu-vertical {
            background-color: var(--bg-secondary-color) !important;
            transition: var(--transition);
        }
        
        .wy-side-nav-search input[type="text"] {
            border-color: var(--border-color);
            background-color: var(--bg-tertiary-color);
            color: var(--text-color);
        }
        
        .wy-menu-vertical a {
            color: var(--text-color);
        }
        
        .wy-menu-vertical a:hover {
            background-color: var(--bg-tertiary-color);
        }
        
        .rst-content div[class^="highlight"] {
            background-color: var(--code-bg);
            border-color: var(--border-color);
        }
        
        .rst-content code {
            background-color: var(--code-bg);
            color: var(--code-color);
            border-color: var(--border-color);
        }
        
        .rst-content table.docutils {
            border-color: var(--table-border-color);
        }
        
        .rst-content table.docutils thead th {
            background-color: var(--table-header-bg);
            color: var(--text-color);
            border-color: var(--table-border-color);
        }
        
        .rst-content table.docutils td {
            border-color: var(--table-border-color);
        }
        
        .rst-content .admonition {
            background-color: var(--admonition-bg);
            border-color: var(--border-color);
        }
        
        .rst-content .note {
            background-color: var(--admonition-note-bg);
        }
        
        .rst-content .warning {
            background-color: var(--admonition-warning-bg);
        }
        
        .rst-content .caution, .rst-content .danger {
            background-color: var(--admonition-caution-bg);
        }
        
        .rst-content .tip, .rst-content .important {
            background-color: var(--admonition-success-bg);
        }
        
        a {
            color: var(--link-color);
            transition: color 0.2s;
        }
        
        a:hover {
            color: var(--link-hover-color);
        }
        
        /* Theme toggle button */
        .theme-toggle-btn {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background-color: var(--bg-tertiary-color);
            border: 1px solid var(--border-color);
            cursor: pointer;
            box-shadow: 0 2px 4px var(--shadow-color);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background-color 0.2s;
        }
        
        .theme-toggle-btn:hover {
            background-color: var(--bg-secondary-color);
        }
        
        @media (max-width: 768px) {
            .theme-toggle-btn {
                top: 15px;
                right: 15px;
                width: 35px;
                height: 35px;
            }
        }
    `;
    
    document.head.appendChild(styleEl);
}

/**
 * Create the theme toggle button
 */
function createThemeToggle() {
    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'theme-toggle-btn';
    toggleBtn.id = 'theme-toggle';
    toggleBtn.setAttribute('aria-label', 'Toggle theme');
    toggleBtn.setAttribute('title', 'Toggle light/dark theme');
    
    // Create SVG icons for light and dark mode
    const lightIcon = `
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="theme-icon light-icon">
            <circle cx="12" cy="12" r="5"></circle>
            <line x1="12" y1="1" x2="12" y2="3"></line>
            <line x1="12" y1="21" x2="12" y2="23"></line>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
            <line x1="1" y1="12" x2="3" y2="12"></line>
            <line x1="21" y1="12" x2="23" y2="12"></line>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
        </svg>
    `;
    
    const darkIcon = `
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="theme-icon dark-icon">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
        </svg>
    `;
    
    // Set initial icon based on current theme
    toggleBtn.innerHTML = document.documentElement.getAttribute('data-theme') === 'dark' ? lightIcon : darkIcon;
    
    // Add click event to toggle theme
    toggleBtn.addEventListener('click', function() {
        toggleTheme();
    });
    
    // Add button to body
    document.body.appendChild(toggleBtn);
}

/**
 * Toggle between light and dark themes
 */
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    // Update data-theme attribute
    document.documentElement.setAttribute('data-theme', newTheme);
    
    // Update button icon
    const toggleBtn = document.getElementById('theme-toggle');
    if (toggleBtn) {
        const lightIcon = `
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="theme-icon light-icon">
                <circle cx="12" cy="12" r="5"></circle>
                <line x1="12" y1="1" x2="12" y2="3"></line>
                <line x1="12" y1="21" x2="12" y2="23"></line>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                <line x1="1" y1="12" x2="3" y2="12"></line>
                <line x1="21" y1="12" x2="23" y2="12"></line>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
            </svg>
        `;
        
        const darkIcon = `
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="theme-icon dark-icon">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
            </svg>
        `;
        
        toggleBtn.innerHTML = newTheme === 'dark' ? lightIcon : darkIcon;
    }
    
    // Store theme preference
    if (typeof localStorage !== 'undefined') {
        try {
            localStorage.setItem('theme', newTheme);
        } catch (e) {
            console.warn('Unable to store theme preference: ', e);
        }
    }
    
    // Dispatch theme change event
    const event = new CustomEvent('themeChanged', { detail: { theme: newTheme } });
    document.dispatchEvent(event);
}

/**
 * Initialize theme based on user preference or system settings
 */
function initializeTheme() {
    // Check for stored preference
    let theme = 'light';
    
    if (typeof localStorage !== 'undefined') {
        try {
            const storedTheme = localStorage.getItem('theme');
            if (storedTheme) {
                theme = storedTheme;
            } else {
                // Check system preference
                if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                    theme = 'dark';
                }
            }
        } catch (e) {
            console.warn('Unable to get theme preference: ', e);
        }
    }
    
    // Set initial theme
    document.documentElement.setAttribute('data-theme', theme);
    
    // Update button icon
    const toggleBtn = document.getElementById('theme-toggle');
    if (toggleBtn) {
        const lightIcon = `
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="theme-icon light-icon">
                <circle cx="12" cy="12" r="5"></circle>
                <line x1="12" y1="1" x2="12" y2="3"></line>
                <line x1="12" y1="21" x2="12" y2="23"></line>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                <line x1="1" y1="12" x2="3" y2="12"></line>
                <line x1="21" y1="12" x2="23" y2="12"></line>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
            </svg>
        `;
        
        const darkIcon = `
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="theme-icon dark-icon">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
            </svg>
        `;
        
        toggleBtn.innerHTML = theme === 'dark' ? lightIcon : darkIcon;
    }
    
    // Listen for system theme changes
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
            // Only change if the user hasn't set a preference
            if (!localStorage.getItem('theme')) {
                const newTheme = e.matches ? 'dark' : 'light';
                document.documentElement.setAttribute('data-theme', newTheme);
                
                // Update button icon
                const toggleBtn = document.getElementById('theme-toggle');
                if (toggleBtn) {
                    const lightIcon = `
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="theme-icon light-icon">
                            <circle cx="12" cy="12" r="5"></circle>
                            <line x1="12" y1="1" x2="12" y2="3"></line>
                            <line x1="12" y1="21" x2="12" y2="23"></line>
                            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                            <line x1="1" y1="12" x2="3" y2="12"></line>
                            <line x1="21" y1="12" x2="23" y2="12"></line>
                            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
                        </svg>
                    `;
                    
                    const darkIcon = `
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="theme-icon dark-icon">
                            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                        </svg>
                    `;
                    
                    toggleBtn.innerHTML = newTheme === 'dark' ? lightIcon : darkIcon;
                }
            }
        });
    }
} 