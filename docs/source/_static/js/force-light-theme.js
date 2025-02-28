/**
 * force-light-theme.js - Ensures light theme is always set as default
 */

// Apply light theme immediately
(function() {
    // Remove dark theme class if present
    document.documentElement.classList.remove('dark-theme');
    
    // Set light theme in localStorage
    localStorage.setItem('theme', 'light');
    
    // Add a class to indicate light theme is forced
    document.documentElement.classList.add('light-theme-forced');
    
    // Create and add a meta tag for color scheme
    var meta = document.createElement('meta');
    meta.name = 'color-scheme';
    meta.content = 'light';
    document.head.appendChild(meta);
    
    // Run again when DOM is loaded to ensure it takes effect
    document.addEventListener('DOMContentLoaded', function() {
        document.documentElement.classList.remove('dark-theme');
        localStorage.setItem('theme', 'light');
    });
    
    // Override any attempt to set dark theme from system preferences
    window.matchMedia('(prefers-color-scheme: dark)').addListener(function() {
        document.documentElement.classList.remove('dark-theme');
        localStorage.setItem('theme', 'light');
    });
})(); 