/**
 * Main JavaScript for Memories-Dev Documentation
 * 
 * This file loads all the consolidated JavaScript files in the correct order.
 */

// Load dark mode functionality first
document.addEventListener('DOMContentLoaded', function() {
  // Load dark mode script
  loadScript('dark-mode.js', function() {
    console.log('Dark mode script loaded');
    
    // Load diagrams script after dark mode is initialized
    loadScript('diagrams.js', function() {
      console.log('Diagrams script loaded');
    });
    
    // Load book features script
    loadScript('book-features.js', function() {
      console.log('Book features script loaded');
    });
  });
});

/**
 * Load a script dynamically
 * 
 * @param {string} filename - The filename to load from the consolidated directory
 * @param {Function} callback - Callback function to execute when script is loaded
 */
function loadScript(filename, callback) {
  const script = document.createElement('script');
  script.src = `_static/js/consolidated/${filename}`;
  script.async = true;
  
  script.onload = function() {
    if (callback) callback();
  };
  
  script.onerror = function() {
    console.error(`Failed to load script: ${filename}`);
  };
  
  document.head.appendChild(script);
} 