// Lazy Loader for memories-dev documentation
// Improves performance by loading images and content only when needed

document.addEventListener('DOMContentLoaded', function() {
    // Lazy loading for images
    setupLazyImages();
    
    // Fix depth issues in navigation
    fixNavigationDepth();
    
    // Improve math rendering
    enhanceMathRendering();
    
    // Handle mobile navigation
    setupMobileNavigation();
    
    // Add smooth scrolling
    setupSmoothScrolling();
    
    // Fix z-index issues
    fixZIndexIssues();
    
    // Fix color inconsistencies
    fixColorInconsistencies();
    
    // Ensure tooltips work properly
    setupTooltips();
    
    // Fix "On This Page" section
    fixOnThisPageSection();
});

/**
 * Setup lazy loading for images
 */
function setupLazyImages() {
    // Register intersection observer for lazy loading
    const lazyImages = [].slice.call(document.querySelectorAll('img.lazy'));
    
    if ('IntersectionObserver' in window) {
        let lazyImageObserver = new IntersectionObserver(function(entries, observer) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    let lazyImage = entry.target;
                    if (lazyImage.dataset.src) {
                        lazyImage.src = lazyImage.dataset.src;
                        lazyImage.classList.remove('lazy');
                        lazyImageObserver.unobserve(lazyImage);
                    }
                }
            });
        });

        lazyImages.forEach(function(lazyImage) {
            lazyImageObserver.observe(lazyImage);
        });
    } else {
        // Fallback for browsers without intersection observer
        let active = false;

        const lazyLoad = function() {
            if (active === false) {
                active = true;

                setTimeout(function() {
                    lazyImages.forEach(function(lazyImage) {
                        if ((lazyImage.getBoundingClientRect().top <= window.innerHeight && lazyImage.getBoundingClientRect().bottom >= 0) && getComputedStyle(lazyImage).display !== 'none') {
                            if (lazyImage.dataset.src) {
                                lazyImage.src = lazyImage.dataset.src;
                                lazyImage.classList.remove('lazy');
                            }

                            lazyImages = lazyImages.filter(function(image) {
                                return image !== lazyImage;
                            });

                            if (lazyImages.length === 0) {
                                document.removeEventListener('scroll', lazyLoad);
                                window.removeEventListener('resize', lazyLoad);
                                window.removeEventListener('orientationchange', lazyLoad);
                            }
                        }
                    });

                    active = false;
                }, 200);
            }
        };

        document.addEventListener('scroll', lazyLoad);
        window.addEventListener('resize', lazyLoad);
        window.addEventListener('orientationchange', lazyLoad);
        window.addEventListener('load', lazyLoad);
    }
}

/**
 * Fix navigation depth issues
 */
function fixNavigationDepth() {
    // Get all navigation items
    const navItems = document.querySelectorAll('.wy-menu-vertical li');
    
    // Add click handlers to toggle visibility
    navItems.forEach(item => {
        // Only add to items that have children
        const hasChildren = item.querySelector('ul') !== null;
        
        if (hasChildren && !item.classList.contains('current')) {
            // Hide children by default
            const childList = item.querySelector('ul');
            if (childList) {
                childList.style.display = 'none';
            }
            
            // Add click handler
            const link = item.querySelector('a');
            if (link) {
                link.addEventListener('click', function(e) {
                    // Don't prevent navigation on leaf nodes
                    if (hasChildren) {
                        e.preventDefault();
                        e.stopPropagation();
                        const childList = item.querySelector('ul');
                        const isVisible = childList.style.display !== 'none';
                        childList.style.display = isVisible ? 'none' : 'block';
                        
                        // Toggle expanded/collapsed state
                        item.classList.toggle('expanded', !isVisible);
                    }
                });
            }
        }
    });
}

/**
 * Enhance math rendering
 */
function enhanceMathRendering() {
    // Add scroll to math elements that are too wide
    const mathElements = document.querySelectorAll('.math');
    mathElements.forEach(element => {
        if (element.scrollWidth > element.clientWidth) {
            element.style.overflowX = 'auto';
            element.style.display = 'block';
            element.style.maxWidth = '100%';
            element.style.margin = '10px 0';
            element.style.padding = '5px';
            element.style.border = '1px solid #e5e5e5';
            element.style.borderRadius = '4px';
        }
    });
}

/**
 * Setup mobile navigation
 */
function setupMobileNavigation() {
    const menuButton = document.querySelector('.wy-nav-top i');
    if (menuButton) {
        menuButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const sidebar = document.querySelector('.wy-nav-side');
            const content = document.querySelector('.wy-nav-content-wrap');
            
            sidebar.classList.toggle('shift');
            content.classList.toggle('shift');
            
            // Add overlay if sidebar is open
            if (sidebar.classList.contains('shift')) {
                addOverlay();
            } else {
                removeOverlay();
            }
        });
    }
    
    // Close menu when clicking outside
    document.addEventListener('click', function(e) {
        const sidebar = document.querySelector('.wy-nav-side');
        const menuButton = document.querySelector('.wy-nav-top i');
        
        if (sidebar && sidebar.classList.contains('shift') && 
            !sidebar.contains(e.target) && e.target !== menuButton) {
            sidebar.classList.remove('shift');
            
            const content = document.querySelector('.wy-nav-content-wrap');
            if (content) {
                content.classList.remove('shift');
            }
            
            removeOverlay();
        }
    });
}

/**
 * Add overlay when mobile menu is open
 */
function addOverlay() {
    let overlay = document.getElementById('mobile-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'mobile-overlay';
        overlay.style.position = 'fixed';
        overlay.style.top = '0';
        overlay.style.left = '0';
        overlay.style.right = '0';
        overlay.style.bottom = '0';
        overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
        overlay.style.zIndex = '199'; // Just below sidebar
        document.body.appendChild(overlay);
        
        overlay.addEventListener('click', function() {
            const sidebar = document.querySelector('.wy-nav-side');
            const content = document.querySelector('.wy-nav-content-wrap');
            
            sidebar.classList.remove('shift');
            content.classList.remove('shift');
            removeOverlay();
        });
    }
}

/**
 * Remove overlay
 */
function removeOverlay() {
    const overlay = document.getElementById('mobile-overlay');
    if (overlay) {
        overlay.parentNode.removeChild(overlay);
    }
}

/**
 * Setup smooth scrolling for anchor links
 */
function setupSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                e.preventDefault();
                window.scrollTo({
                    top: targetElement.offsetTop - 70, // Account for fixed header
                    behavior: 'smooth'
                });
                
                // Update URL without reloading the page
                history.pushState(null, null, targetId);
            }
        });
    });
}

/**
 * Fix z-index issues in the UI
 */
function fixZIndexIssues() {
    // Ensure content is properly layered
    const contentElements = [
        {selector: '.wy-nav-content', zIndex: 1},
        {selector: '.wy-nav-top', zIndex: 300},
        {selector: '.wy-side-scroll', zIndex: 200},
        {selector: '.rst-versions', zIndex: 400},
        {selector: '.rst-content .note, .rst-content .attention, .rst-content .caution', zIndex: 10},
        {selector: '.wy-alert, .rst-content .note', zIndex: 10}
    ];
    
    contentElements.forEach(item => {
        const elements = document.querySelectorAll(item.selector);
        elements.forEach(el => {
            el.style.zIndex = item.zIndex;
        });
    });
    
    // Fix dropdown menu layering
    const dropdowns = document.querySelectorAll('.wy-dropdown, .wy-dropdown-menu');
    dropdowns.forEach(dropdown => {
        dropdown.style.zIndex = 500;
    });
}

/**
 * Fix color inconsistencies
 */
function fixColorInconsistencies() {
    // Primary colors
    const primaryColor = '#3b82f6'; // Blue color from the hero button
    const darkBgColor = '#0f172a'; // Dark bg from hero gradient start
    
    // Update colors for consistency
    const elementsToFix = [
        {selector: '.wy-menu-vertical a:hover', property: 'color', value: '#ffffff'},
        {selector: '.wy-menu-vertical li.current > a', property: 'borderLeftColor', value: primaryColor},
        {selector: '.btn-info', property: 'backgroundColor', value: primaryColor},
        {selector: '.wy-side-nav-search input[type="text"]', property: 'borderColor', value: primaryColor},
        {selector: '.rst-content .note', property: 'backgroundColor', value: '#f0f9ff'},
        {selector: '.rst-content .note .admonition-title', property: 'backgroundColor', value: primaryColor}
    ];
    
    elementsToFix.forEach(item => {
        const elements = document.querySelectorAll(item.selector);
        elements.forEach(el => {
            el.style[item.property] = item.value;
        });
    });
}

/**
 * Setup tooltips for better UI
 */
function setupTooltips() {
    // Find all elements with title attributes
    const elementsWithTitles = document.querySelectorAll('[title]:not(a)');
    
    elementsWithTitles.forEach(element => {
        element.addEventListener('mouseenter', function(e) {
            const title = this.getAttribute('title');
            if (!title) return;
            
            // Create tooltip
            let tooltip = document.createElement('div');
            tooltip.className = 'custom-tooltip';
            tooltip.textContent = title;
            
            // Style the tooltip
            tooltip.style.position = 'absolute';
            tooltip.style.backgroundColor = '#333';
            tooltip.style.color = '#fff';
            tooltip.style.padding = '5px 10px';
            tooltip.style.borderRadius = '4px';
            tooltip.style.fontSize = '12px';
            tooltip.style.zIndex = 1000;
            tooltip.style.pointerEvents = 'none';
            tooltip.style.opacity = '0';
            tooltip.style.transition = 'opacity 0.3s';
            
            // Add to body
            document.body.appendChild(tooltip);
            
            // Position tooltip
            const rect = this.getBoundingClientRect();
            tooltip.style.left = `${rect.left + window.scrollX + rect.width / 2 - tooltip.offsetWidth / 2}px`;
            tooltip.style.top = `${rect.top + window.scrollY - tooltip.offsetHeight - 10}px`;
            
            // Show tooltip
            setTimeout(() => { tooltip.style.opacity = '1'; }, 10);
            
            // Remove title to prevent default tooltip
            this.setAttribute('data-title', title);
            this.removeAttribute('title');
            
            // Remove tooltip on mouseleave
            const tooltipElement = tooltip;
            this.addEventListener('mouseleave', function onMouseLeave() {
                tooltipElement.style.opacity = '0';
                
                setTimeout(() => {
                    if (tooltipElement.parentNode) {
                        tooltipElement.parentNode.removeChild(tooltipElement);
                    }
                }, 300);
                
                this.setAttribute('title', this.getAttribute('data-title'));
                this.removeAttribute('data-title');
                
                this.removeEventListener('mouseleave', onMouseLeave);
            });
        });
    });
}



// Apply lazy loading to all images added to the document dynamically
const mutationCallback = function(mutationsList) {
    for (let mutation of mutationsList) {
        if (mutation.type === 'childList') {
            mutation.addedNodes.forEach(node => {
                if (node.nodeType === 1) { // ELEMENT_NODE
                    const images = node.querySelectorAll('img:not(.lazy)');
                    images.forEach(img => {
                        if (!img.classList.contains('lazy') && !img.classList.contains('no-lazy')) {
                            img.classList.add('lazy');
                            img.dataset.src = img.src;
                            img.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"%3E%3C/svg%3E';
                        }
                    });
                }
            });
        }
    }
};

// Start observing the document for dynamic content changes
const observer = new MutationObserver(mutationCallback);
observer.observe(document.body, { childList: true, subtree: true }); 