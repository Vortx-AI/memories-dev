/**
 * Memory Codex - Enhanced Book Experience JavaScript
 * 
 * This script provides interactive features to enhance the documentation's 
 * book-like experience, focusing on readability, navigation, and engagement.
 */

// Main initialization function
function initBookExperience() {
  // Check if we're on a documentation page
  if (document.querySelector('.book-container')) {
    // Initialize all book experience enhancements
    initBookCover();
    initChapterTransitions();
    initProgressTracker();
    initBookmarkSystem();
    initPageNotes();
    enhanceCodeBlocks();
    initJourneyMap();
    calculateReadingTime();
    
    // Check if we're on a page that should have Earth visualization
    if (document.body.classList.contains('earth-visualization-page') || 
        window.location.pathname.includes('memory_architecture') ||
        window.location.pathname.includes('memory_types')) {
      initEarthVisualization();
    }
    
    // Make the interface responsive
    initResponsiveUI();
  }
}

/**
 * Initialize 3D book cover for homepage
 */
function initBookCover() {
  const bookCover = document.querySelector('.book-cover-3d');
  if (!bookCover) return;
  
  // Add hover effect on non-touch devices
  if (!('ontouchstart' in window)) {
    bookCover.addEventListener('mousemove', (e) => {
      const xAxis = (window.innerWidth / 2 - e.pageX) / 25;
      const yAxis = (window.innerHeight / 2 - e.pageY) / 25;
      bookCover.style.transform = `rotateY(${xAxis}deg) rotateX(${yAxis}deg)`;
    });
    
    bookCover.addEventListener('mouseenter', () => {
      bookCover.style.transition = 'none';
    });
    
    bookCover.addEventListener('mouseleave', () => {
      bookCover.style.transition = 'all 0.5s ease';
      bookCover.style.transform = 'rotateY(-30deg) rotateX(0deg)';
    });
  }
  
  // Auto-open the book after a delay
  setTimeout(() => {
    bookCover.classList.add('open');
  }, 1500);
  
  // Make book clickable to open
  bookCover.addEventListener('click', () => {
    bookCover.classList.add('open');
    
    // Smooth scroll to journey map if it exists
    const journeyMap = document.querySelector('.journey-map');
    if (journeyMap) {
      setTimeout(() => {
        journeyMap.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }, 700);
    }
  });
}

/**
 * Initialize smooth transitions between chapters
 */
function initChapterTransitions() {
  // Handle clicks on next/prev buttons
  const navButtons = document.querySelectorAll('.prev-button, .next-button');
  
  navButtons.forEach(button => {
    button.addEventListener('click', function(e) {
      e.preventDefault();
      const currentPage = document.querySelector('.book-content');
      const targetUrl = this.getAttribute('href');
      
      // Don't apply transition if it's a mobile device
      if (window.innerWidth <= 768 || 'ontouchstart' in window) {
        window.location.href = targetUrl;
        return;
      }
      
      // Apply page turning animation
      if (currentPage) {
        currentPage.classList.add('page-turning');
        
        setTimeout(() => {
          window.location.href = targetUrl;
        }, 400);
      } else {
        window.location.href = targetUrl;
      }
    });
  });
  
  // Add page loaded animation
  if (!sessionStorage.getItem('pageVisited')) {
    const content = document.querySelector('.book-content');
    if (content) {
      content.classList.add('page-loaded');
      // Mark that page was visited, so animation only happens first time
      sessionStorage.setItem('pageVisited', 'true');
    }
  }
}

/**
 * Initialize reading progress tracker
 */
function initProgressTracker() {
  const progressBar = document.querySelector('.progress-bar');
  if (!progressBar) return;
  
  // Function to update the progress bar based on scroll position
  function updateProgress() {
    const windowHeight = window.innerHeight;
    const fullHeight = document.body.scrollHeight;
    const scrolled = window.scrollY;
    
    // Calculate how far scrolled as a percentage
    const percentScrolled = (scrolled / (fullHeight - windowHeight)) * 100;
    progressBar.style.width = percentScrolled + '%';
    
    // Save reading progress in sessionStorage
    const path = window.location.pathname;
    sessionStorage.setItem('readingProgress-' + path, scrolled);
  }
  
  // Update progress when scrolling
  window.addEventListener('scroll', updateProgress);
  
  // Restore reading progress when page loads
  function restoreReadingProgress() {
    const path = window.location.pathname;
    const savedPosition = sessionStorage.getItem('readingProgress-' + path);
    
    if (savedPosition) {
      // Restore scroll position smoothly
      setTimeout(() => {
        window.scrollTo({
          top: parseInt(savedPosition),
          behavior: 'auto'
        });
      }, 100);
    }
  }
  
  // Initialize progress
  updateProgress();
  if (!window.location.hash) {
    restoreReadingProgress();
  }
}

/**
 * Initialize the bookmark system
 */
function initBookmarkSystem() {
  // Check for existing bookmarks in localStorage
  let bookmarks = JSON.parse(localStorage.getItem('memoryCodexBookmarks')) || {};
  
  // Create bookmark button if we're on a chapter page
  const bookContainer = document.querySelector('.book-page');
  const pageTitle = document.title;
  const path = window.location.pathname;
  
  if (bookContainer) {
    // Create bookmark button
    const bookmarkButton = document.createElement('button');
    bookmarkButton.className = 'bookmark-button';
    bookmarkButton.innerHTML = '🔖';
    bookmarkButton.title = 'Bookmark this chapter';
    bookmarkButton.setAttribute('aria-label', 'Bookmark this chapter');
    
    // Check if this page is already bookmarked
    if (bookmarks[path]) {
      bookmarkButton.classList.add('active');
      bookmarkButton.title = 'Remove bookmark';
    }
    
    // Toggle bookmark on click
    bookmarkButton.addEventListener('click', () => {
      if (bookmarks[path]) {
        // Remove bookmark
        delete bookmarks[path];
        bookmarkButton.classList.remove('active');
        bookmarkButton.title = 'Bookmark this chapter';
        showNotification('Bookmark removed');
      } else {
        // Add bookmark
        bookmarks[path] = {
          title: pageTitle.replace(' — Memory Codex', ''),
          timestamp: new Date().toISOString()
        };
        bookmarkButton.classList.add('active');
        bookmarkButton.title = 'Remove bookmark';
        showNotification('Bookmark added');
      }
      
      // Save bookmarks to localStorage
      localStorage.setItem('memoryCodexBookmarks', JSON.stringify(bookmarks));
      updateBookmarksList();
    });
    
    // Add bookmark button to the page
    bookContainer.appendChild(bookmarkButton);
    
    // Create bookmarks toggle button
    const bookmarksToggle = document.createElement('button');
    bookmarksToggle.className = 'bookmarks-toggle';
    bookmarksToggle.innerHTML = '🔖';
    bookmarksToggle.title = 'View bookmarks';
    bookmarksToggle.setAttribute('aria-label', 'View bookmarks');
    
    // Create bookmarks menu
    const bookmarksMenu = document.createElement('div');
    bookmarksMenu.className = 'bookmarks-menu';
    
    // Add header
    const bookmarksHeader = document.createElement('div');
    bookmarksHeader.className = 'bookmarks-header';
    bookmarksHeader.innerHTML = '<h3>Your Bookmarks</h3>';
    
    // Add close button
    const closeButton = document.createElement('button');
    closeButton.className = 'close-bookmarks';
    closeButton.innerHTML = '×';
    closeButton.title = 'Close bookmarks';
    closeButton.setAttribute('aria-label', 'Close bookmarks');
    bookmarksHeader.appendChild(closeButton);
    
    // Add bookmarks list container
    const bookmarksList = document.createElement('div');
    bookmarksList.className = 'bookmarks-list';
    
    // Assemble bookmarks menu
    bookmarksMenu.appendChild(bookmarksHeader);
    bookmarksMenu.appendChild(bookmarksList);
    
    // Add to body
    document.body.appendChild(bookmarksToggle);
    document.body.appendChild(bookmarksMenu);
    
    // Toggle bookmarks menu
    bookmarksToggle.addEventListener('click', () => {
      bookmarksMenu.classList.toggle('active');
    });
    
    // Close bookmarks menu
    closeButton.addEventListener('click', () => {
      bookmarksMenu.classList.remove('active');
    });
    
    // Close bookmarks on click outside
    document.addEventListener('click', (e) => {
      if (!bookmarksMenu.contains(e.target) && e.target !== bookmarksToggle) {
        bookmarksMenu.classList.remove('active');
      }
    });
    
    // Initial bookmarks list
    updateBookmarksList();
    
    // Save current chapter as last read
    localStorage.setItem('lastReadChapter', path);
    localStorage.setItem('lastReadTitle', pageTitle.replace(' — Memory Codex', ''));
    
    // Function to update the bookmarks list
    function updateBookmarksList() {
      bookmarksList.innerHTML = '';
      bookmarks = JSON.parse(localStorage.getItem('memoryCodexBookmarks')) || {};
      
      // Sort bookmarks by latest first
      const sortedBookmarks = Object.entries(bookmarks).sort((a, b) => {
        return new Date(b[1].timestamp) - new Date(a[1].timestamp);
      });
      
      if (sortedBookmarks.length === 0) {
        bookmarksList.innerHTML = '<div class="no-bookmarks">No bookmarks yet</div>';
        return;
      }
      
      // Create bookmark items
      sortedBookmarks.forEach(([path, data]) => {
        const bookmarkItem = document.createElement('div');
        bookmarkItem.className = 'bookmark-item';
        
        const bookmarkLink = document.createElement('a');
        bookmarkLink.className = 'bookmark-link';
        bookmarkLink.href = path;
        bookmarkLink.textContent = data.title;
        
        const removeButton = document.createElement('button');
        removeButton.className = 'remove-bookmark';
        removeButton.innerHTML = '×';
        removeButton.title = 'Remove bookmark';
        removeButton.setAttribute('aria-label', 'Remove bookmark');
        
        removeButton.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          
          // Remove bookmark
          delete bookmarks[path];
          localStorage.setItem('memoryCodexBookmarks', JSON.stringify(bookmarks));
          
          // Update button state if we're on this page
          if (path === window.location.pathname) {
            bookmarkButton.classList.remove('active');
            bookmarkButton.title = 'Bookmark this chapter';
          }
          
          // Update list
          updateBookmarksList();
          showNotification('Bookmark removed');
        });
        
        bookmarkItem.appendChild(bookmarkLink);
        bookmarkItem.appendChild(removeButton);
        bookmarksList.appendChild(bookmarkItem);
      });
    }
  }
}

/**
 * Show a notification message
 */
function showNotification(message) {
  // Check if notification already exists
  let notification = document.querySelector('.book-notification');
  
  // Create new notification if needed
  if (!notification) {
    notification = document.createElement('div');
    notification.className = 'book-notification';
    document.body.appendChild(notification);
  }
  
  // Set message and show
  notification.textContent = message;
  notification.classList.add('active');
  
  // Hide after delay
  setTimeout(() => {
    notification.classList.remove('active');
    
    // Remove from DOM after animation
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 300);
  }, 2000);
}

/**
 * Initialize page notes styling
 */
function initPageNotes() {
  // Style margin notes
  const notes = document.querySelectorAll('.note, .admonition');
  
  notes.forEach(note => {
    // Skip if already processed
    if (note.classList.contains('margin-note')) return;
    
    // Convert to margin note
    note.classList.add('margin-note');
    
    // Add icon based on note type
    const title = note.querySelector('.admonition-title');
    if (title) {
      let icon = '📝';
      
      if (note.classList.contains('warning')) icon = '⚠️';
      if (note.classList.contains('danger')) icon = '🚨';
      if (note.classList.contains('tip')) icon = '💡';
      if (note.classList.contains('important')) icon = '📢';
      
      title.innerHTML = icon + ' ' + title.innerHTML;
    }
  });
}

/**
 * Enhance code blocks with copy buttons and language indicators
 */
function enhanceCodeBlocks() {
  const codeBlocks = document.querySelectorAll('pre');
  
  codeBlocks.forEach(block => {
    // Skip if already processed
    if (block.classList.contains('enhanced')) return;
    block.classList.add('enhanced');
    
    // Determine language
    let language = 'code';
    const classes = block.className.split(' ');
    
    classes.forEach(className => {
      if (className.startsWith('language-')) {
        language = className.replace('language-', '');
      } else if (className.includes('highlight-')) {
        language = className.replace('highlight-', '');
      }
    });
    
    // Add language indicator
    const languageIndicator = document.createElement('span');
    languageIndicator.className = 'code-language';
    languageIndicator.textContent = language;
    block.appendChild(languageIndicator);
    
    // Add copy button
    const copyButton = document.createElement('button');
    copyButton.className = 'copy-code-button';
    copyButton.textContent = 'Copy';
    block.appendChild(copyButton);
    
    // Copy functionality
    copyButton.addEventListener('click', () => {
      // Get text from pre block
      const code = block.querySelector('code') 
        ? block.querySelector('code').innerText 
        : block.innerText;
      
      // Remove the button text from the copied content
      const textToCopy = code.replace('Copy', '').trim();
      
      // Copy to clipboard
      navigator.clipboard.writeText(textToCopy).then(() => {
        // Visual feedback
        copyButton.textContent = 'Copied!';
        setTimeout(() => {
          copyButton.textContent = 'Copy';
        }, 2000);
      }).catch(err => {
        console.error('Could not copy text: ', err);
        copyButton.textContent = 'Error!';
        setTimeout(() => {
          copyButton.textContent = 'Copy';
        }, 2000);
      });
    });
  });
}

/**
 * Initialize journey map with hover effects and clickable stages
 */
function initJourneyMap() {
  const journeyStages = document.querySelectorAll('.journey-stage');
  if (journeyStages.length === 0) return;
  
  // Get current page path
  const currentPath = window.location.pathname;
  
  journeyStages.forEach(stage => {
    // Check if this stage is current
    const targetPath = stage.getAttribute('data-target');
    if (targetPath && currentPath.includes(targetPath)) {
      stage.classList.add('current');
    }
    
    // Add hover animation for non-touch devices
    if (!('ontouchstart' in window)) {
      stage.addEventListener('mouseenter', () => {
        stage.classList.add('active');
      });
      
      stage.addEventListener('mouseleave', () => {
        stage.classList.remove('active');
      });
    }
    
    // Make stages clickable
    if (targetPath) {
      stage.style.cursor = 'pointer';
      stage.addEventListener('click', () => {
        window.location.href = targetPath;
      });
    }
  });
}

/**
 * Calculate and display reading time
 */
function calculateReadingTime() {
  const contentElement = document.querySelector('.book-content');
  const readingTimeElement = document.querySelector('.reading-time-value');
  
  if (contentElement && readingTimeElement) {
    // Get text content and count words
    const text = contentElement.textContent;
    const wordCount = text.split(/\s+/).length;
    
    // Calculate reading time (average reading speed: 200 words per minute)
    const readingTimeMinutes = Math.ceil(wordCount / 200);
    
    // Update reading time element
    readingTimeElement.textContent = `${readingTimeMinutes} min read`;
  }
}

/**
 * Initialize Earth visualization on specific pages
 */
function initEarthVisualization() {
  // Create Earth visualization container
  const container = document.createElement('div');
  container.className = 'earth-visualization';
  
  // Create Earth elements
  container.innerHTML = `
    <div class="earth-sphere">
      <div class="earth-surface"></div>
      <div class="atmosphere"></div>
      <div class="clouds"></div>
      <div class="grid"></div>
    </div>
  `;
  
  // Add to page, after first heading if possible
  const firstHeading = document.querySelector('h1');
  if (firstHeading && firstHeading.nextElementSibling) {
    firstHeading.parentNode.insertBefore(container, firstHeading.nextElementSibling);
  } else {
    // Fallback - add to beginning of content
    const content = document.querySelector('.book-content');
    if (content && content.firstChild) {
      content.insertBefore(container, content.firstChild);
    }
  }
  
  // Add rotation effect
  const earth = container.querySelector('.earth-sphere');
  if (earth) {
    if (!('ontouchstart' in window)) {
      document.addEventListener('mousemove', (e) => {
        const xAxis = (window.innerWidth / 2 - e.pageX) / 50;
        const yAxis = (window.innerHeight / 2 - e.pageY) / 50;
        earth.style.transform = `rotateY(${xAxis}deg) rotateX(${yAxis}deg)`;
      });
    }
    
    // Add subtle auto-rotation if no hover
    let autoRotation = 0;
    function rotateEarth() {
      if (!earth.style.transform) { // Only auto-rotate if not transformed by mousemove
        autoRotation += 0.1;
        earth.style.transform = `rotateY(${autoRotation}deg)`;
      }
      requestAnimationFrame(rotateEarth);
    }
    rotateEarth();
  }
}

/**
 * Initialize responsive UI adjustments
 */
function initResponsiveUI() {
  // Check for mobile devices
  const isMobile = window.innerWidth <= 768 || 'ontouchstart' in window;
  
  if (isMobile) {
    // Adjust journey map for mobile
    const journeyMap = document.querySelector('.journey-map');
    if (journeyMap) {
      const stages = journeyMap.querySelectorAll('.journey-stage');
      // Show only first 3 stages on mobile with a button to show more
      if (stages.length > 3) {
        let visibleCount = 0;
        stages.forEach((stage, index) => {
          if (stage.classList.contains('current')) {
            // Always show current stage
            stage.style.display = 'block';
            visibleCount++;
          } else if (visibleCount < 2) {
            // Show two other stages
            stage.style.display = 'block';
            visibleCount++;
          } else {
            // Hide remaining stages
            stage.style.display = 'none';
          }
        });
        
        // Add "Show more" button if we have hidden stages
        if (visibleCount < stages.length) {
          const showMoreButton = document.createElement('button');
          showMoreButton.className = 'show-more-stages';
          showMoreButton.innerHTML = 'Show all stages';
          showMoreButton.style.width = '100%';
          showMoreButton.style.padding = '10px';
          showMoreButton.style.marginTop = '10px';
          showMoreButton.style.background = 'var(--codex-deep-forest)';
          showMoreButton.style.color = 'white';
          showMoreButton.style.border = 'none';
          showMoreButton.style.borderRadius = '4px';
          showMoreButton.style.cursor = 'pointer';
          
          showMoreButton.addEventListener('click', () => {
            stages.forEach(stage => {
              stage.style.display = 'block';
            });
            showMoreButton.style.display = 'none';
          });
          
          journeyMap.appendChild(showMoreButton);
        }
      }
    }
    
    // Improve tap targets
    const smallButtons = document.querySelectorAll('.copy-code-button, .remove-bookmark');
    smallButtons.forEach(button => {
      button.style.padding = '10px';
    });
  }
  
  // Handle window resize
  window.addEventListener('resize', () => {
    // Recalculate reading time
    calculateReadingTime();
    
    // Adjust UI for new screen size
    const newIsMobile = window.innerWidth <= 768;
    if (newIsMobile !== isMobile) {
      // Reload to apply different UI rules
      window.location.reload();
    }
  });
}

// Initialize the book experience when the page loads
document.addEventListener('DOMContentLoaded', initBookExperience);

// If jQuery is available, use ready function as fallback
if (typeof jQuery !== 'undefined') {
  jQuery(document).ready(function() {
    initBookExperience();
  });
} 