/**
 * Navigation Enhancer for Memories-Dev Documentation
 * 
 * This script improves the navigation experience by:
 * 1. Adding collapsible sections to the sidebar
 * 2. Highlighting the current section
 * 3. Adding smooth scrolling for anchor links
 * 4. Creating an auto-hiding mobile navigation
 */
document.addEventListener('DOMContentLoaded', function() {
    // Enhanced sidebar navigation
    enhanceSidebar();
    
    // Add smooth scrolling for anchor links
    addSmoothScrolling();
    
    // Add mobile navigation improvements
    enhanceMobileNav();
    
    // Add active section tracking
    trackActiveSection();
});

/**
 * Enhance sidebar navigation with collapsible sections and visual improvements
 */
function enhanceSidebar() {
    const sidebar = document.querySelector('.wy-nav-side');
    if (!sidebar) return;
    
    // Add collapse/expand functionality to sections
    const sectionHeadings = sidebar.querySelectorAll('.caption-text');
    sectionHeadings.forEach(heading => {
        // Make headings clickable to collapse/expand their section
        heading.style.cursor = 'pointer';
        
        // Add toggle icons
        const icon = document.createElement('span');
        icon.classList.add('section-toggle');
        icon.innerHTML = '▼';
        icon.style.marginLeft = '6px';
        icon.style.fontSize = '0.7em';
        heading.appendChild(icon);
        
        // Get the list that follows this heading
        const list = heading.parentElement.nextElementSibling;
        if (!list) return;
        
        // Set up the click handler for collapsing/expanding
        heading.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Toggle visibility
            if (list.style.display === 'none') {
                list.style.display = 'block';
                icon.innerHTML = '▼';
            } else {
                list.style.display = 'none';
                icon.innerHTML = '▶';
            }
        });
    });
    
    // Highlight current section more prominently
    const currentItems = sidebar.querySelectorAll('li.current');
    currentItems.forEach(item => {
        item.style.borderLeft = '3px solid #3b82f6';
        item.style.paddingLeft = '5px';
    });
}

/**
 * Add smooth scrolling for anchor links
 */
function addSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            // Get the target element
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (!targetElement) return;
            
            // Prevent default behavior
            e.preventDefault();
            
            // Scroll smoothly to the target
            targetElement.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
            
            // Update URL hash without jumping
            history.pushState(null, null, targetId);
        });
    });
}

/**
 * Enhance mobile navigation
 */
function enhanceMobileNav() {
    const navButton = document.querySelector('.wy-nav-top button');
    const sidebar = document.querySelector('.wy-nav-side');
    
    if (!navButton || !sidebar) return;
    
    // Add auto-hide functionality for mobile nav
    document.addEventListener('click', function(e) {
        // If sidebar is open and click is outside sidebar
        if (sidebar.classList.contains('shift') && 
            !sidebar.contains(e.target) && 
            e.target !== navButton) {
            
            // Close the sidebar
            sidebar.classList.remove('shift');
            document.querySelector('.wy-nav-content-wrap').classList.remove('shift');
        }
    });
    
    // Add swipe to close on mobile
    let touchStartX = 0;
    sidebar.addEventListener('touchstart', function(e) {
        touchStartX = e.changedTouches[0].screenX;
    }, false);
    
    sidebar.addEventListener('touchend', function(e) {
        const touchEndX = e.changedTouches[0].screenX;
        const diff = touchStartX - touchEndX;
        
        // If swiped left more than 50px, close the sidebar
        if (diff > 50) {
            sidebar.classList.remove('shift');
            document.querySelector('.wy-nav-content-wrap').classList.remove('shift');
        }
    }, false);
}

/**
 * Track and highlight the current active section based on scroll position
 */
function trackActiveSection() {
    // Only apply to content pages
    if (document.querySelectorAll('.section').length <= 1) return;
    
    const sections = document.querySelectorAll('div.section[id]');
    const navLinks = document.querySelectorAll('.wy-menu-vertical li a');
    
    // Throttled scroll handler
    let ticking = false;
    
    window.addEventListener('scroll', function() {
        if (!ticking) {
            window.requestAnimationFrame(function() {
                highlightActiveSections(sections, navLinks);
                ticking = false;
            });
            ticking = true;
        }
    });
    
    // Initial highlighting
    highlightActiveSections(sections, navLinks);
}

/**
 * Highlight the active sections in the navigation
 */
function highlightActiveSections(sections, navLinks) {
    // Determine which section is currently in view
    let currentSection = null;
    const scrollPosition = window.scrollY + 100; // Offset for better UX
    
    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.offsetHeight;
        
        if (scrollPosition >= sectionTop && 
            scrollPosition < sectionTop + sectionHeight) {
            currentSection = section.id;
        }
    });
    
    // Update navigation highlight
    if (currentSection) {
        navLinks.forEach(link => {
            // Remove current highlighting
            link.classList.remove('active-section');
            
            // Add highlighting to current section
            const href = link.getAttribute('href');
            if (href && href.includes('#' + currentSection)) {
                link.classList.add('active-section');
            }
        });
    }
}
