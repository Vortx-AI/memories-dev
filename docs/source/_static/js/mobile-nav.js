/**
 * Mobile navigation enhancements for memories-dev documentation
 * This script improves the mobile experience with the Sphinx RTD theme
 */
document.addEventListener('DOMContentLoaded', function() {
  // Mobile menu toggle
  var menuButton = document.querySelector('.wy-nav-top i');
  if (menuButton) {
    menuButton.addEventListener('click', function() {
      var sidebar = document.querySelector('.wy-nav-side');
      var content = document.querySelector('.wy-nav-content-wrap');
      
      sidebar.classList.toggle('shift');
      content.classList.toggle('shift');
    });
  }
  
  // Close menu when clicking outside
  var contentWrap = document.querySelector('.wy-nav-content-wrap');
  if (contentWrap) {
    contentWrap.addEventListener('click', function(e) {
      var sidebar = document.querySelector('.wy-nav-side');
      if (sidebar && sidebar.classList.contains('shift') && e.target !== menuButton) {
        sidebar.classList.remove('shift');
        contentWrap.classList.remove('shift');
      }
    });
  }
  
  // Add touch-friendly behavior to dropdown menus
  var touchMenuItems = document.querySelectorAll('.wy-menu-vertical li.toctree-l1:has(ul)');
  touchMenuItems.forEach(function(item) {
    var link = item.querySelector('a');
    if (window.innerWidth <= 768 && link) {
      link.addEventListener('touchend', function(e) {
        if (!item.classList.contains('current')) {
          e.preventDefault();
          item.classList.add('current');
        }
      });
    }
  });
  
  // Fix font size issues on small screens
  if (window.innerWidth <= 480) {
    document.body.classList.add('mobile-view');
  }
}); 