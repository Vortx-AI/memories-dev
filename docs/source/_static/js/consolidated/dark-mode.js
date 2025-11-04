/**
 * Consolidated Dark Mode JavaScript for Memories-Dev Documentation
 * 
 * This file handles dark mode toggle functionality.
 */

(function() {
  // Wait for DOM to be fully loaded
  document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing dark mode functionality');
    initDarkMode();
  });
  
  /**
   * Initialize dark mode functionality
   */
  function initDarkMode() {
    // Create toggle button if it doesn't exist
    if (!document.getElementById('dark-mode-toggle')) {
      createToggleButton();
    }
    
    // Check for saved preference
    const savedTheme = localStorage.getItem('theme');
    
    // Check for system preference if no saved preference
    if (!savedTheme) {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      if (prefersDark) {
        document.body.classList.add('dark-theme');
      }
    } else if (savedTheme === 'dark') {
      document.body.classList.add('dark-theme');
    }
    
    // Update button state
    updateToggleButton();
    
    // Listen for system preference changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
      if (!localStorage.getItem('theme')) {
        if (e.matches) {
          document.body.classList.add('dark-theme');
        } else {
          document.body.classList.remove('dark-theme');
        }
        updateToggleButton();
        notifyThemeChange();
      }
    });
  }
  
  /**
   * Create dark mode toggle button
   */
  function createToggleButton() {
    const button = document.createElement('button');
    button.id = 'dark-mode-toggle';
    button.setAttribute('aria-label', 'Toggle dark mode');
    button.setAttribute('title', 'Toggle dark mode');
    
    // Create light icon (sun)
    const lightIcon = document.createElement('span');
    lightIcon.className = 'light-icon';
    lightIcon.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
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
    
    // Create dark icon (moon)
    const darkIcon = document.createElement('span');
    darkIcon.className = 'dark-icon';
    darkIcon.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
      </svg>
    `;
    
    // Add icons to button
    button.appendChild(lightIcon);
    button.appendChild(darkIcon);
    
    // Add click event
    button.addEventListener('click', function() {
      document.body.classList.toggle('dark-theme');
      
      // Save preference
      if (document.body.classList.contains('dark-theme')) {
        localStorage.setItem('theme', 'dark');
      } else {
        localStorage.setItem('theme', 'light');
      }
      
      updateToggleButton();
      notifyThemeChange();
    });
    
    // Add to document
    document.body.appendChild(button);
  }
  
  /**
   * Update toggle button state
   */
  function updateToggleButton() {
    const button = document.getElementById('dark-mode-toggle');
    if (!button) return;
    
    if (document.body.classList.contains('dark-theme')) {
      button.setAttribute('aria-label', 'Switch to light mode');
      button.setAttribute('title', 'Switch to light mode');
    } else {
      button.setAttribute('aria-label', 'Switch to dark mode');
      button.setAttribute('title', 'Switch to dark mode');
    }
  }
  
  /**
   * Notify other scripts about theme change
   */
  function notifyThemeChange() {
    // Create and dispatch a custom event
    const event = new CustomEvent('themeChanged', {
      detail: {
        isDarkMode: document.body.classList.contains('dark-theme')
      }
    });
    document.dispatchEvent(event);
  }
})(); 