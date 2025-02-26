// Theme Toggle for memories-dev documentation
document.addEventListener('DOMContentLoaded', function() {
    // Create theme toggle button
    createThemeToggle();
    
    // Initialize theme based on user preference or saved setting
    initializeTheme();
    
    // Add theme toggle event listener
    setupThemeToggleListener();
});

/**
 * Create theme toggle button in the navigation
 */
function createThemeToggle() {
    // Create toggle container
    const toggleContainer = document.createElement('div');
    toggleContainer.className = 'theme-toggle-container';
    toggleContainer.setAttribute('aria-label', 'Toggle between dark and light mode');
    toggleContainer.setAttribute('role', 'button');
    toggleContainer.setAttribute('tabindex', '0');
    
    // Create toggle switch
    const toggleSwitch = document.createElement('label');
    toggleSwitch.className = 'theme-toggle-switch';
    
    // Create checkbox input
    const toggleInput = document.createElement('input');
    toggleInput.type = 'checkbox';
    toggleInput.id = 'theme-toggle';
    toggleInput.className = 'theme-toggle-input';
    
    // Create toggle slider
    const toggleSlider = document.createElement('span');
    toggleSlider.className = 'theme-toggle-slider';
    
    // Create icons for light and dark mode
    const lightIcon = document.createElement('span');
    lightIcon.className = 'theme-toggle-icon light-icon';
    lightIcon.innerHTML = '☀️';
    lightIcon.setAttribute('aria-hidden', 'true');
    
    const darkIcon = document.createElement('span');
    darkIcon.className = 'theme-toggle-icon dark-icon';
    darkIcon.innerHTML = '🌙';
    darkIcon.setAttribute('aria-hidden', 'true');
    
    // Assemble toggle components
    toggleSlider.appendChild(lightIcon);
    toggleSlider.appendChild(darkIcon);
    toggleSwitch.appendChild(toggleInput);
    toggleSwitch.appendChild(toggleSlider);
    toggleContainer.appendChild(toggleSwitch);
    
    // Add toggle to the navigation
    const navContent = document.querySelector('.wy-side-nav-search');
    if (navContent) {
        navContent.appendChild(toggleContainer);
    } else {
        // Fallback to body if nav not found
        document.body.insertBefore(toggleContainer, document.body.firstChild);
    }
    
    // Add styles for theme toggle
    addThemeToggleStyles();
}

/**
 * Add CSS styles for theme toggle
 */
function addThemeToggleStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .theme-toggle-container {
            display: flex;
            justify-content: center;
            margin-top: 1rem;
            margin-bottom: 1rem;
        }
        
        .theme-toggle-switch {
            position: relative;
            display: inline-block;
            width: 60px;
            height: 30px;
        }
        
        .theme-toggle-input {
            opacity: 0;
            width: 0;
            height: 0;
        }
        
        .theme-toggle-slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #2c3e50;
            transition: .4s;
            border-radius: 30px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 5px;
        }
        
        .theme-toggle-slider:before {
            position: absolute;
            content: "";
            height: 22px;
            width: 22px;
            left: 4px;
            bottom: 4px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
            z-index: 2;
        }
        
        .theme-toggle-input:checked + .theme-toggle-slider {
            background-color: #4285f4;
        }
        
        .theme-toggle-input:checked + .theme-toggle-slider:before {
            transform: translateX(30px);
        }
        
        .theme-toggle-icon {
            z-index: 1;
            font-size: 14px;
        }
        
        .light-icon {
            margin-right: 5px;
        }
        
        .dark-icon {
            margin-left: 5px;
        }
        
        /* Light theme variables */
        :root[data-theme="light"] {
            --primary-color: #ffffff;
            --primary-light: #f8f9fa;
            --primary-dark: #e9ecef;
            --accent-color: #4285f4;
            --accent-light: #5c9aff;
            --accent-dark: #3367d6;
            --success-color: #34a853;
            --warning-color: #fbbc05;
            --danger-color: #ea4335;
            --info-color: #24c1e0;
            --text-color: #202124;
            --text-muted: #5f6368;
            --border-color: #dadce0;
            --code-bg: #f8f9fa;
            --code-color: #202124;
            
            /* Code syntax highlighting colors for light theme */
            --code-keyword: #0b8043;
            --code-function: #1a73e8;
            --code-string: #e37400;
            --code-number: #c5221f;
            --code-comment: #5f6368;
            --code-operator: #0b8043;
            --code-class: #1a73e8;
            --code-variable: #202124;
            --code-property: #24c1e0;
        }
        
        /* Dark theme is the default in custom.css */
    `;
    
    document.head.appendChild(style);
}

/**
 * Initialize theme based on user preference or saved setting
 */
function initializeTheme() {
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme');
    
    // Check for system preference if no saved theme
    const prefersDarkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Set initial theme
    if (savedTheme === 'light') {
        setLightTheme();
    } else if (savedTheme === 'dark' || prefersDarkMode) {
        setDarkTheme();
    } else {
        setDarkTheme(); // Default to dark theme
    }
    
    // Update toggle switch state
    const toggleInput = document.getElementById('theme-toggle');
    if (toggleInput) {
        toggleInput.checked = document.documentElement.getAttribute('data-theme') === 'dark';
    }
}

/**
 * Set up event listener for theme toggle
 */
function setupThemeToggleListener() {
    const toggleInput = document.getElementById('theme-toggle');
    if (toggleInput) {
        toggleInput.addEventListener('change', function() {
            if (this.checked) {
                setDarkTheme();
            } else {
                setLightTheme();
            }
        });
        
        // Add keyboard support
        const toggleContainer = document.querySelector('.theme-toggle-container');
        if (toggleContainer) {
            toggleContainer.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    toggleInput.checked = !toggleInput.checked;
                    
                    // Trigger change event
                    const event = new Event('change');
                    toggleInput.dispatchEvent(event);
                }
            });
        }
    }
}

/**
 * Set light theme
 */
function setLightTheme() {
    document.documentElement.setAttribute('data-theme', 'light');
    localStorage.setItem('theme', 'light');
    
    // Update toggle state
    const toggleInput = document.getElementById('theme-toggle');
    if (toggleInput) {
        toggleInput.checked = false;
    }
}

/**
 * Set dark theme
 */
function setDarkTheme() {
    document.documentElement.setAttribute('data-theme', 'dark');
    localStorage.setItem('theme', 'dark');
    
    // Update toggle state
    const toggleInput = document.getElementById('theme-toggle');
    if (toggleInput) {
        toggleInput.checked = true;
    }
} 