/**
 * Theme Toggle for Memories-Dev Documentation
 * 
 * This script adds light/dark theme switching capabilities:
 * 1. Adds a theme toggle button to the navigation
 * 2. Respects user system preferences
 * 3. Saves theme preference in localStorage
 * 4. Provides smooth transitions between themes
 */
document.addEventListener('DOMContentLoaded', function() {
    // Add theme toggle button
    addThemeToggle();
    
    // Initialize theme based on saved preference or system preference
    initializeTheme();
});

/**
 * Add theme toggle button to the navigation
 */
function addThemeToggle() {
    // Create theme toggle container
    const toggleContainer = document.createElement('div');
    toggleContainer.className = 'theme-toggle-container';
    toggleContainer.style.position = 'absolute';
    toggleContainer.style.top = '10px';
    toggleContainer.style.right = '10px';
    toggleContainer.style.zIndex = '1001';
    
    // Create toggle button
    const toggleButton = document.createElement('button');
    toggleButton.className = 'theme-toggle-button';
    toggleButton.setAttribute('aria-label', 'Toggle theme');
    toggleButton.style.background = 'transparent';
    toggleButton.style.border = '1px solid rgba(255, 255, 255, 0.2)';
    toggleButton.style.borderRadius = '50%';
    toggleButton.style.width = '40px';
    toggleButton.style.height = '40px';
    toggleButton.style.display = 'flex';
    toggleButton.style.alignItems = 'center';
    toggleButton.style.justifyContent = 'center';
    toggleButton.style.cursor = 'pointer';
    toggleButton.style.color = 'white';
    toggleButton.style.fontSize = '20px';
    toggleButton.style.transition = 'all 0.2s ease';
    
    // Button hover effect
    toggleButton.addEventListener('mouseenter', function() {
        this.style.transform = 'scale(1.1)';
        this.style.boxShadow = '0 0 10px rgba(59, 130, 246, 0.5)';
    });
    
    toggleButton.addEventListener('mouseleave', function() {
        this.style.transform = 'scale(1)';
        this.style.boxShadow = 'none';
    });
    
    // Set initial icon based on current theme
    const isDarkMode = document.documentElement.classList.contains('dark-theme');
    toggleButton.innerHTML = isDarkMode ? '☀️' : '🌙';
    
    // Add click event to toggle theme
    toggleButton.addEventListener('click', function() {
        toggleTheme();
    });
    
    // Add button to container
    toggleContainer.appendChild(toggleButton);
    
    // Add container to page
    const searchContainer = document.querySelector('.wy-side-nav-search');
    if (searchContainer) {
        searchContainer.appendChild(toggleContainer);
    }
}

/**
 * Initialize theme based on saved preference or system preference
 */
function initializeTheme() {
    // Add transition styles for smooth theme changes
    const style = document.createElement('style');
    style.textContent = `
        body, .wy-nav-content, .wy-nav-side, .wy-side-nav-search, code, pre {
            transition: background-color 0.3s ease, color 0.3s ease;
        }
        
        /* Dark theme styles */
        html.dark-theme body {
            color: #e0e0e0;
            background-color: #121212;
        }
        
        html.dark-theme .wy-nav-content {
            background-color: #1e1e1e;
            color: #e0e0e0;
        }
        
        html.dark-theme .wy-nav-side {
            background-color: #0f172a;
        }
        
        html.dark-theme .wy-side-nav-search {
            background-color: #0c1221;
        }
        
        html.dark-theme .wy-menu-vertical a {
            color: #b0b0b0;
        }
        
        html.dark-theme .wy-menu-vertical a:hover {
            background-color: rgba(255, 255, 255, 0.1);
        }
        
        html.dark-theme code {
            background-color: #2d2d2d;
            border-color: #444;
            color: #e0e0e0;
        }
        
        html.dark-theme pre {
            background-color: #2d2d2d;
            border-color: #444;
            color: #e0e0e0;
        }
        
        html.dark-theme .highlight {
            background-color: #2d2d2d;
        }
        
        html.dark-theme table.docutils td, 
        html.dark-theme table.docutils th {
            border-color: #444;
        }
        
        html.dark-theme table.docutils thead th {
            background-color: #333;
        }
        
        html.dark-theme table.docutils {
            border-color: #444;
        }
        
        html.dark-theme a {
            color: #7eb6ff;
        }
        
        html.dark-theme .btn-primary {
            background-color: #2563eb;
        }
        
        html.dark-theme .rst-content .note {
            background-color: #1c2434;
            border-color: #3b82f6;
        }
        
        html.dark-theme .rst-content .warning {
            background-color: #433426;
            border-color: #f59e0b;
        }
    `;
    document.head.appendChild(style);
    
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('memories_dev_theme');
    
    if (savedTheme) {
        // Apply saved theme
        if (savedTheme === 'dark') {
            enableDarkTheme();
        } else {
            enableLightTheme();
        }
    } else {
        // Check for system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            enableDarkTheme();
        } else {
            enableLightTheme();
        }
        
        // Listen for system preference changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', event => {
            if (event.matches) {
                enableDarkTheme();
            } else {
                enableLightTheme();
            }
        });
    }
}

/**
 * Toggle between light and dark themes
 */
function toggleTheme() {
    const isDarkTheme = document.documentElement.classList.contains('dark-theme');
    
    if (isDarkTheme) {
        enableLightTheme();
    } else {
        enableDarkTheme();
    }
}

/**
 * Enable dark theme
 */
function enableDarkTheme() {
    document.documentElement.classList.add('dark-theme');
    
    // Update toggle button icon
    const toggleButton = document.querySelector('.theme-toggle-button');
    if (toggleButton) {
        toggleButton.innerHTML = '☀️';  // Sun icon for switching to light mode
    }
    
    // Save preference
    localStorage.setItem('memories_dev_theme', 'dark');
}

/**
 * Enable light theme
 */
function enableLightTheme() {
    document.documentElement.classList.remove('dark-theme');
    
    // Update toggle button icon
    const toggleButton = document.querySelector('.theme-toggle-button');
    if (toggleButton) {
        toggleButton.innerHTML = '🌙';  // Moon icon for switching to dark mode
    }
    
    // Save preference
    localStorage.setItem('memories_dev_theme', 'light');
}
