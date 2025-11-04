/**
 * Consolidated Book Features JavaScript for Memories-Dev Documentation
 * 
 * This file handles book-like features such as chapter navigation,
 * reading progress, and decorative elements.
 */

(function() {
  // Wait for DOM to be fully loaded
  document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing book features');
    
    // Setup reading progress indicator
    setupReadingProgress();
    
    // Setup chapter navigation
    setupChapterNavigation();
    
    // Setup section highlighting
    setupSectionHighlighting();
    
    // Setup smooth scrolling
    setupSmoothScrolling();
    
    // Setup mobile navigation
    setupMobileNavigation();
    
    // Add chapter numbers
    addChapterNumbers();
    
    // Enhance figures and tables
    enhanceFiguresAndTables();
    
    // Setup page turn effect
    setupPageTurnEffect();
    
    // Add book formatting
    addBookFormatting();
  });
  
  /**
   * Setup reading progress indicator
   */
  function setupReadingProgress() {
    // Create progress bar if it doesn't exist
    if (!document.getElementById('reading-progress')) {
      const progressBar = document.createElement('div');
      progressBar.id = 'reading-progress';
      progressBar.style.position = 'fixed';
      progressBar.style.top = '0';
      progressBar.style.left = '0';
      progressBar.style.height = '3px';
      progressBar.style.backgroundColor = 'var(--accent-color)';
      progressBar.style.zIndex = '1000';
      progressBar.style.width = '0%';
      progressBar.style.transition = 'width 0.2s';
      document.body.appendChild(progressBar);
    }
    
    // Update progress on scroll
    function updateProgress() {
      const windowHeight = window.innerHeight;
      const documentHeight = document.documentElement.scrollHeight - windowHeight;
      const scrollTop = window.scrollY;
      const progress = (scrollTop / documentHeight) * 100;
      
      document.getElementById('reading-progress').style.width = `${progress}%`;
    }
    
    // Add scroll event listener
    window.addEventListener('scroll', updateProgress);
    
    // Initial update
    updateProgress();
  }
  
  /**
   * Setup chapter navigation
   */
  function setupChapterNavigation() {
    // Get next/prev links
    const nextLink = document.querySelector('.rst-footer-buttons .btn-neutral.float-right');
    const prevLink = document.querySelector('.rst-footer-buttons .btn-neutral.float-left');
    
    // Add page turn classes
    if (nextLink) {
      nextLink.classList.add('page-turn', 'page-turn-forward');
      nextLink.addEventListener('click', function(e) {
        e.preventDefault();
        
        // Add page turning animation
        document.body.classList.add('page-turning-forward');
        
        // Navigate after animation
        setTimeout(function() {
          window.location.href = nextLink.getAttribute('href');
        }, 300);
      });
    }
    
    if (prevLink) {
      prevLink.classList.add('page-turn', 'page-turn-backward');
      prevLink.addEventListener('click', function(e) {
        e.preventDefault();
        
        // Add page turning animation
        document.body.classList.add('page-turning-backward');
        
        // Navigate after animation
        setTimeout(function() {
          window.location.href = prevLink.getAttribute('href');
        }, 300);
      });
    }
  }
  
  /**
   * Setup section highlighting
   */
  function setupSectionHighlighting() {
    const sections = document.querySelectorAll('.section');
    
    // Highlight section on scroll
    function highlightSection() {
      const scrollPosition = window.scrollY + 100;
      
      sections.forEach(function(section) {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.offsetHeight;
        
        if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
          // Remove highlight from all sections
          sections.forEach(s => s.classList.remove('active-section'));
          
          // Add highlight to current section
          section.classList.add('active-section');
          
          // Update TOC
          const id = section.id;
          if (id) {
            const tocLink = document.querySelector(`.wy-menu-vertical a[href="#${id}"]`);
            if (tocLink) {
              document.querySelectorAll('.wy-menu-vertical a').forEach(a => a.classList.remove('current-section'));
              tocLink.classList.add('current-section');
            }
          }
        }
      });
    }
    
    // Add scroll event listener
    window.addEventListener('scroll', highlightSection);
    
    // Initial highlight
    highlightSection();
  }
  
  /**
   * Setup smooth scrolling
   */
  function setupSmoothScrolling() {
    // Get all internal links
    const internalLinks = document.querySelectorAll('a[href^="#"]');
    
    internalLinks.forEach(function(link) {
      link.addEventListener('click', function(e) {
        const href = this.getAttribute('href');
        
        if (href !== '#') {
          e.preventDefault();
          
          const targetElement = document.querySelector(href);
          if (targetElement) {
            targetElement.scrollIntoView({
              behavior: 'smooth',
              block: 'start'
            });
          }
        }
      });
    });
  }
  
  /**
   * Setup mobile navigation
   */
  function setupMobileNavigation() {
    // Get mobile nav toggle
    const navToggle = document.querySelector('.wy-nav-top i');
    
    if (navToggle) {
      navToggle.addEventListener('click', function() {
        document.querySelector('.wy-nav-side').classList.toggle('shift');
        document.querySelector('.wy-nav-content-wrap').classList.toggle('shift');
      });
    }
  }
  
  /**
   * Add chapter numbers
   */
  function addChapterNumbers() {
    // Get all h1 headings
    const headings = document.querySelectorAll('h1');
    
    headings.forEach(function(heading, index) {
      // Skip if already has chapter number
      if (heading.querySelector('.chapter-number')) return;
      
      // Create chapter number element
      const chapterNumber = document.createElement('div');
      chapterNumber.className = 'chapter-number';
      chapterNumber.textContent = `Chapter ${index + 1}`;
      
      // Insert before heading text
      heading.insertBefore(chapterNumber, heading.firstChild);
      
      // Add chapter title class to parent
      const parent = heading.parentElement;
      if (parent && parent.tagName.toLowerCase() === 'div') {
        parent.classList.add('chapter-title');
        
        // Add decorative line
        const line = document.createElement('div');
        line.className = 'decorative-line';
        parent.appendChild(line);
      }
    });
  }
  
  /**
   * Enhance figures and tables
   */
  function enhanceFiguresAndTables() {
    // Enhance figures
    const figures = document.querySelectorAll('.figure');
    
    figures.forEach(function(figure) {
      // Add click to enlarge
      const img = figure.querySelector('img');
      if (img) {
        img.style.cursor = 'pointer';
        
        img.addEventListener('click', function() {
          // Create modal
          const modal = document.createElement('div');
          modal.style.position = 'fixed';
          modal.style.top = '0';
          modal.style.left = '0';
          modal.style.width = '100%';
          modal.style.height = '100%';
          modal.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
          modal.style.zIndex = '1000';
          modal.style.display = 'flex';
          modal.style.alignItems = 'center';
          modal.style.justifyContent = 'center';
          
          // Create enlarged image
          const enlargedImg = document.createElement('img');
          enlargedImg.src = img.src;
          enlargedImg.style.maxWidth = '90%';
          enlargedImg.style.maxHeight = '90%';
          enlargedImg.style.boxShadow = '0 0 20px rgba(0, 0, 0, 0.5)';
          
          // Add to modal
          modal.appendChild(enlargedImg);
          
          // Close on click
          modal.addEventListener('click', function() {
            document.body.removeChild(modal);
          });
          
          // Add to body
          document.body.appendChild(modal);
        });
      }
    });
    
    // Enhance tables
    const tables = document.querySelectorAll('table.docutils');
    
    tables.forEach(function(table) {
      // Add table wrapper for scrolling
      const wrapper = document.createElement('div');
      wrapper.style.overflowX = 'auto';
      wrapper.style.marginBottom = '1rem';
      
      // Replace table with wrapper containing table
      table.parentNode.insertBefore(wrapper, table);
      wrapper.appendChild(table);
    });
  }
  
  /**
   * Setup page turn effect
   */
  function setupPageTurnEffect() {
    // Add page turn effect to navigation links
    const links = document.querySelectorAll('a:not([href^="#"]):not([href^="javascript"])');
    
    links.forEach(function(link) {
      // Skip external links
      if (link.hostname !== window.location.hostname) return;
      
      // Skip links in the navigation
      if (link.closest('.wy-menu-vertical') || link.closest('.wy-side-nav-search') || link.closest('.rst-footer-buttons')) return;
      
      link.addEventListener('click', function(e) {
        const href = this.getAttribute('href');
        
        // Skip if href is empty or just #
        if (!href || href === '#') return;
        
        e.preventDefault();
        
        // Add page turning animation
        document.body.classList.add('page-turning-forward');
        
        // Navigate after animation
        setTimeout(function() {
          window.location.href = href;
        }, 300);
      });
    });
  }
  
  /**
   * Add book formatting
   */
  function addBookFormatting() {
    // Add first letter styling
    const sections = document.querySelectorAll('.section');
    
    sections.forEach(function(section) {
      const firstParagraph = section.querySelector('p');
      if (firstParagraph) {
        firstParagraph.classList.add('first-paragraph');
      }
    });
    
    // Add chapter labels
    const h2Elements = document.querySelectorAll('h2');
    
    h2Elements.forEach(function(h2) {
      // Skip if already has chapter label
      if (h2.querySelector('.chapter-label')) return;
      
      // Create chapter label
      const label = document.createElement('span');
      label.className = 'chapter-label';
      label.textContent = 'Section';
      
      // Insert before heading text
      h2.insertBefore(label, h2.firstChild);
      
      // Add space after label
      h2.insertBefore(document.createTextNode(' '), label.nextSibling);
    });
    
    // Add book sections
    const admonitions = document.querySelectorAll('.admonition');
    
    admonitions.forEach(function(admonition) {
      admonition.classList.add('book-section');
    });
  }
})(); 