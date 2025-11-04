/**
 * dark-mode-toggle.js - Dark mode toggle functionality
 */

(function() {
    // Initialize on DOM load
    document.addEventListener('DOMContentLoaded', function() {
        initDarkMode();
    });
    
    function initDarkMode() {
        // Check for saved preference
        const savedTheme = localStorage.getItem('theme');
        
        // Apply saved theme or system preference
        if (savedTheme === 'dark') {
            document.documentElement.classList.add('dark-theme');
        } else if (savedTheme === 'light') {
            document.documentElement.classList.remove('dark-theme');
        } else {
            // If no saved preference, check system preference
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                document.documentElement.classList.add('dark-theme');
            }
        }
        
        // Create toggle button if it doesn't exist yet
        if (!document.getElementById('dark-mode-toggle')) {
            createToggleButton();
        }
        
        // Listen for system preference changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
                // Only apply system preference if no saved preference
                if (!localStorage.getItem('theme')) {
                    if (e.matches) {
                        document.documentElement.classList.add('dark-theme');
                    } else {
                        document.documentElement.classList.remove('dark-theme');
                    }
                    
                    // Notify other scripts about theme change
                    notifyThemeChange();
                }
            });
        }
    }
    
    function createToggleButton() {
        // Create button
        const darkModeToggle = document.createElement('button');
        darkModeToggle.id = 'dark-mode-toggle';
        darkModeToggle.setAttribute('aria-label', 'Toggle dark mode');
        darkModeToggle.innerHTML = '<span class="light-icon">🌙</span><span class="dark-icon">☀️</span>';
        darkModeToggle.title = 'Toggle dark mode';
        
        // Add click handler
        darkModeToggle.addEventListener('click', function() {
            document.documentElement.classList.toggle('dark-theme');
            const isDark = document.documentElement.classList.contains('dark-theme');
            
            // Save preference
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
            
            // Notify other scripts about theme change
            notifyThemeChange();
        });
        
        // Add to sidebar
        const sideNav = document.querySelector('.wy-side-nav-search');
        if (sideNav) {
            sideNav.appendChild(darkModeToggle);
        } else {
            // If sidebar not found, try adding to top navigation (mobile view)
            const topNav = document.querySelector('.wy-nav-top');
            if (topNav) {
                darkModeToggle.classList.add('mobile');
                topNav.appendChild(darkModeToggle);
            } else {
                // Last resort: add to body
                document.body.appendChild(darkModeToggle);
                darkModeToggle.classList.add('floating');
                darkModeToggle.style.position = 'fixed';
                darkModeToggle.style.bottom = '20px';
                darkModeToggle.style.right = '20px';
                darkModeToggle.style.zIndex = '1000';
            }
        }
    }
    
    function notifyThemeChange() {
        // Dispatch event for other scripts to detect theme change
        const isDark = document.documentElement.classList.contains('dark-theme');
        document.dispatchEvent(new CustomEvent('themeToggled', {
            detail: { isDark: isDark }
        }));
        
        // Update mermaid diagrams if mermaid is loaded
        if (typeof window.mermaid !== 'undefined' && typeof window.renderAllMermaidDiagrams === 'function') {
            setTimeout(function() {
                window.renderAllMermaidDiagrams(true);
            }, 100);
        }
        
        // Update MathJax if loaded
        if (typeof window.MathJax !== 'undefined' && typeof window.MathJax.typeset === 'function') {
            setTimeout(function() {
                window.MathJax.typeset();
            }, 100);
        }
    }
})(); 