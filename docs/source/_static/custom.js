// Simplified Book-like Documentation Experience

document.addEventListener('DOMContentLoaded', function() {
    // Simple back to top button
    addBackToTopButton();
    
    // Simple table of contents highlighting
    enhanceTableOfContents();
    
    // Make tables responsive
    makeTablesResponsive();
    
    // Add simple mobile navigation
    setupMobileNavigation();
});

// Add a simple back to top button
function addBackToTopButton() {
    var backToTopButton = document.createElement('button');
    backToTopButton.innerHTML = '↑';
    backToTopButton.className = 'back-to-top';
    backToTopButton.setAttribute('aria-label', 'Back to top');
    backToTopButton.setAttribute('title', 'Back to top');
    
    document.body.appendChild(backToTopButton);
    
    // Show/hide the button based on scroll position
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTopButton.classList.add('visible');
        } else {
            backToTopButton.classList.remove('visible');
        }
    });
    
    // Scroll to top when clicked
    backToTopButton.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// Enhance table of contents with active section highlighting
function enhanceTableOfContents() {
    // Find all headings in the main content
    var headings = document.querySelectorAll('.section h1, .section h2, .section h3');
    var tocLinks = document.querySelectorAll('.toctree-wrapper a, .contents a');
    
    if (headings.length === 0 || tocLinks.length === 0) return;
    
    // Highlight the current section in the table of contents
    function highlightCurrentSection() {
        var currentHeading = null;
        
        // Find the current heading based on scroll position
        for (var i = 0; i < headings.length; i++) {
            var heading = headings[i];
            var rect = heading.getBoundingClientRect();
            
            if (rect.top <= 100) {
                currentHeading = heading;
            } else {
                break;
            }
        }
        
        if (currentHeading) {
            // Remove highlight from all TOC links
            tocLinks.forEach(function(link) {
                link.classList.remove('active');
            });
            
            // Add highlight to the current TOC link
            var headingId = currentHeading.id;
            var currentLink = document.querySelector('.toctree-wrapper a[href="#' + headingId + '"], .contents a[href="#' + headingId + '"]');
            
            if (currentLink) {
                currentLink.classList.add('active');
            }
        }
    }
    
    // Update on scroll (throttled)
    var scrollTimeout;
    window.addEventListener('scroll', function() {
        if (!scrollTimeout) {
            scrollTimeout = setTimeout(function() {
                highlightCurrentSection();
                scrollTimeout = null;
            }, 100);
        }
    });
    
    // Initial highlight
    highlightCurrentSection();
}

// Make tables responsive
function makeTablesResponsive() {
    var tables = document.querySelectorAll('table');
    
    tables.forEach(function(table) {
        var wrapper = document.createElement('div');
        wrapper.className = 'table-responsive';
        table.parentNode.insertBefore(wrapper, table);
        wrapper.appendChild(table);
    });
}

// Setup mobile navigation
function setupMobileNavigation() {
    var navButton = document.querySelector('.wy-nav-top i');
    var sidebar = document.querySelector('.wy-nav-side');
    var content = document.querySelector('.wy-nav-content-wrap');
    
    if (!navButton || !sidebar || !content) return;
    
    navButton.addEventListener('click', function(e) {
        e.preventDefault();
        sidebar.classList.toggle('shift');
        content.classList.toggle('shift');
        document.body.classList.toggle('nav-open');
    });
    
    // Close menu when clicking on content area in mobile view
    content.addEventListener('click', function() {
        if (window.innerWidth <= 768 && sidebar.classList.contains('shift')) {
            sidebar.classList.remove('shift');
            content.classList.remove('shift');
            document.body.classList.remove('nav-open');
        }
    });
} 