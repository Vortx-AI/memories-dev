/**
 * Consolidated Diagrams JavaScript for Memories-Dev Documentation
 * 
 * This file handles Mermaid diagrams and MathJax rendering.
 */

(function() {
  // Wait for DOM to be fully loaded
  document.addEventListener('DOMContentLoaded', function() {
    console.log('Diagrams.js loaded');
    
    // Initialize MathJax
    initializeMathJax();
    
    // Add window load event to catch any diagrams that might be added dynamically
    window.addEventListener('load', function() {
      setTimeout(function() {
        // Check if Mermaid diagrams need re-rendering
        if (document.querySelectorAll('.mermaid:not([data-processed="true"])').length > 0) {
          console.log('Found unprocessed Mermaid diagrams, rendering...');
          renderAllDiagrams();
        }
        
        // Render math elements
        renderAllMathElements();
      }, 1000);
    });
    
    // Observe DOM changes to catch dynamically added content
    observeDOMChanges();
    
    // Make diagrams expandable
    makeAllDiagramsExpandable();
  });
  
  /**
   * Render all Mermaid diagrams on the page
   */
  function renderAllDiagrams(forceRerender = false) {
    try {
      if (typeof window.mermaid === 'undefined') {
        console.error('Mermaid not available for rendering');
        return;
      }
      
      const diagrams = document.querySelectorAll('.mermaid:not([data-processed="true"])');
      console.log(`Found ${diagrams.length} unprocessed diagrams to render`);
      
      if (diagrams.length > 0) {
        try {
          window.mermaid.init(undefined, diagrams);
        } catch (error) {
          console.error('Error rendering diagrams:', error);
          diagrams.forEach(function(diagram) {
            createFallback(diagram, diagram.textContent, error);
          });
        }
      }
      
      // Make all diagrams expandable after rendering
      makeAllDiagramsExpandable();
    } catch (error) {
      console.error('Error in renderAllDiagrams:', error);
    }
  }
  
  /**
   * Initialize MathJax with proper configuration
   */
  function initializeMathJax() {
    if (typeof window.MathJax === 'undefined') {
      console.log('MathJax not found, loading from CDN');
      loadMathJax();
    } else {
      console.log('MathJax found, configuring');
      configureMathJax();
    }
  }
  
  /**
   * Load MathJax from CDN if not available
   */
  function loadMathJax() {
    window.MathJax = {
      tex: {
        inlineMath: [['\\(', '\\)'], ['$', '$']],
        displayMath: [['\\[', '\\]'], ['$$', '$$']],
        processEscapes: true,
        processEnvironments: true
      },
      options: {
        ignoreHtmlClass: 'tex2jax_ignore',
        processHtmlClass: 'tex2jax_process'
      },
      startup: {
        ready: function() {
          MathJax.startup.defaultReady();
          renderAllMathElements();
        }
      }
    };
    
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js';
    script.async = true;
    
    script.onerror = function() {
      console.error('Failed to load MathJax from CDN');
      // Try alternate CDN
      const altScript = document.createElement('script');
      altScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.0/es5/tex-mml-chtml.min.js';
      altScript.async = true;
      document.head.appendChild(altScript);
    };
    
    document.head.appendChild(script);
  }
  
  /**
   * Configure MathJax with optimal settings
   */
  function configureMathJax() {
    if (typeof window.MathJax !== 'undefined') {
      try {
        if (typeof window.MathJax.typeset === 'function') {
          renderAllMathElements();
        } else if (typeof window.MathJax.Hub !== 'undefined') {
          // MathJax v2
          window.MathJax.Hub.Config({
            tex2jax: {
              inlineMath: [['\\(', '\\)'], ['$', '$']],
              displayMath: [['\\[', '\\]'], ['$$', '$$']],
              processEscapes: true
            }
          });
          window.MathJax.Hub.Queue(['Typeset', window.MathJax.Hub]);
        }
      } catch (error) {
        console.error('Error configuring MathJax:', error);
      }
    }
  }
  
  /**
   * Render all math elements on the page
   */
  function renderAllMathElements() {
    try {
      if (typeof window.MathJax !== 'undefined') {
        if (typeof window.MathJax.typeset === 'function') {
          // MathJax v3
          window.MathJax.typeset();
        } else if (typeof window.MathJax.Hub !== 'undefined') {
          // MathJax v2
          window.MathJax.Hub.Queue(['Typeset', window.MathJax.Hub]);
        }
      }
    } catch (error) {
      console.error('Error rendering math elements:', error);
    }
  }
  
  /**
   * Make all diagrams expandable on click
   */
  function makeAllDiagramsExpandable() {
    const diagrams = document.querySelectorAll('.mermaid');
    
    diagrams.forEach(function(diagram) {
      makeExpandable(diagram);
    });
  }
  
  /**
   * Make a diagram expandable on click
   */
  function makeExpandable(diagram) {
    diagram.addEventListener('click', function() {
      // Toggle expanded state
      if (diagram.classList.contains('expanded')) {
        diagram.classList.remove('expanded');
        document.body.classList.remove('has-expanded-diagram');
      } else {
        diagram.classList.add('expanded');
        document.body.classList.add('has-expanded-diagram');
        
        // Close when clicking outside
        const closeOnClickOutside = function(event) {
          if (!diagram.contains(event.target) && diagram.classList.contains('expanded')) {
            diagram.classList.remove('expanded');
            document.body.classList.remove('has-expanded-diagram');
            document.removeEventListener('click', closeOnClickOutside);
          }
        };
        
        // Add event listener with a slight delay to prevent immediate closing
        setTimeout(function() {
          document.addEventListener('click', closeOnClickOutside);
        }, 100);
      }
    });
  }
  
  /**
   * Create fallback for a failed diagram
   */
  function createFallback(diagram, content, error) {
    const fallback = document.createElement('div');
    fallback.className = 'diagram-fallback';
    
    const header = document.createElement('div');
    header.className = 'diagram-fallback-header';
    header.textContent = 'Diagram rendering failed';
    
    const errorMessage = document.createElement('div');
    errorMessage.className = 'diagram-fallback-error';
    errorMessage.textContent = error ? error.toString() : 'Unknown error';
    
    const pre = document.createElement('pre');
    pre.textContent = content;
    
    fallback.appendChild(header);
    fallback.appendChild(errorMessage);
    fallback.appendChild(pre);
    
    diagram.parentNode.replaceChild(fallback, diagram);
  }
  
  /**
   * Observe DOM changes to catch dynamically added content
   */
  function observeDOMChanges() {
    // Create a MutationObserver to watch for added nodes
    const observer = new MutationObserver(function(mutations) {
      let needsUpdate = false;
      
      mutations.forEach(function(mutation) {
        if (mutation.addedNodes.length > 0) {
          // Check if any added nodes contain diagrams
          mutation.addedNodes.forEach(function(node) {
            if (node.nodeType === 1) { // Element node
              if (node.classList && node.classList.contains('mermaid')) {
                needsUpdate = true;
              } else if (node.querySelectorAll) {
                const diagrams = node.querySelectorAll('.mermaid');
                if (diagrams.length > 0) {
                  needsUpdate = true;
                }
              }
            }
          });
        }
      });
      
      // If new diagrams were added, render them
      if (needsUpdate) {
        setTimeout(function() {
          renderAllDiagrams();
          makeAllDiagramsExpandable();
        }, 100);
      }
    });
    
    // Start observing the document body for changes
    observer.observe(document.body, { childList: true, subtree: true });
  }
})(); 