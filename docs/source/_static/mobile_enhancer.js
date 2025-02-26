// Simplified Mobile Book Experience
document.addEventListener('DOMContentLoaded', function() {
    // Improve readability
    improveReadability();
    
    // Handle mobile navigation
    setupMobileNavigation();
    
    // Simplify tables for mobile
    simplifyTablesForMobile();
    
    // Adjust image sizes for mobile
    adjustImagesForMobile();
});

// Improve readability for mobile devices
function improveReadability() {
    // Apply font size adjustments for small screens
    if (window.innerWidth <= 768) {
        // Add specific mobile styles
        const mobileStyles = document.createElement('style');
        mobileStyles.textContent = `
            @media (max-width: 768px) {
                body {
                    font-size: 16px;
                    line-height: 1.6;
                }
                
                p {
                    font-size: 1rem;
                    margin-bottom: 1em;
                }
                
                ul, ol {
                    padding-left: 1.5em;
                }
                
                .wy-nav-content {
                    padding: 1rem;
                }
                
                pre {
                    padding: 0.75rem;
                    margin: 1rem 0;
                    font-size: 0.85rem;
                }
                
                .admonition {
                    padding: 1rem;
                    margin: 1rem 0;
                }
                
                h1 {
                    font-size: 1.5rem;
                }
                
                h2 {
                    font-size: 1.25rem;
                }
                
                h3 {
                    font-size: 1.1rem;
                }
            }
        `;
        document.head.appendChild(mobileStyles);
    }
}

// Setup mobile navigation
function setupMobileNavigation() {
    const navToggle = document.querySelector('.wy-nav-top i');
    const sidebar = document.querySelector('.wy-nav-side');
    const content = document.querySelector('.wy-nav-content-wrap');
    
    if (!navToggle || !sidebar || !content) return;
    
    // Add click handler for the navigation toggle
    navToggle.addEventListener('click', function(e) {
        e.preventDefault();
        sidebar.classList.toggle('shift');
        content.classList.toggle('shift');
        document.body.classList.toggle('nav-open');
    });
    
    // Close navigation when clicking on content
    content.addEventListener('click', function() {
        if (window.innerWidth <= 768 && sidebar.classList.contains('shift')) {
            sidebar.classList.remove('shift');
            content.classList.remove('shift');
            document.body.classList.remove('nav-open');
        }
    });
    
    // Add swipe functionality for mobile
    let touchStartX = 0;
    let touchEndX = 0;
    
    document.addEventListener('touchstart', function(e) {
        touchStartX = e.changedTouches[0].screenX;
    }, false);
    
    document.addEventListener('touchend', function(e) {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    }, false);
    
    function handleSwipe() {
        const swipeThreshold = 100;
        
        // Right to left swipe (close menu)
        if (touchEndX < touchStartX - swipeThreshold && sidebar.classList.contains('shift')) {
            sidebar.classList.remove('shift');
            content.classList.remove('shift');
            document.body.classList.remove('nav-open');
        }
        
        // Left to right swipe (open menu)
        if (touchEndX > touchStartX + swipeThreshold && !sidebar.classList.contains('shift')) {
            sidebar.classList.add('shift');
            content.classList.add('shift');
            document.body.classList.add('nav-open');
        }
    }
}

// Simplify tables for mobile
function simplifyTablesForMobile() {
    const tables = document.querySelectorAll('table');
    
    if (window.innerWidth <= 768) {
        tables.forEach(function(table) {
            // Already wrapped tables in responsive div in custom.js
            
            // Add data attributes to cells for responsive display
            const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent.trim());
            
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const cells = row.querySelectorAll('td');
                cells.forEach((cell, i) => {
                    if (headers[i]) {
                        cell.setAttribute('data-label', headers[i]);
                    }
                });
            });
        });
    }
}

// Adjust images for mobile
function adjustImagesForMobile() {
    const images = document.querySelectorAll('.rst-content img');
    
    images.forEach(function(img) {
        img.style.maxWidth = '100%';
        img.style.height = 'auto';
        
        // If image is too wide or too tall, make it clickable to view full size
        img.addEventListener('load', function() {
            if (img.naturalWidth > window.innerWidth || img.naturalHeight > window.innerHeight * 0.8) {
                const parent = img.parentNode;
                
                // Skip if already wrapped
                if (parent.tagName === 'A' && parent.classList.contains('image-link')) {
                    return;
                }
                
                // Create link to full image
                const link = document.createElement('a');
                link.href = img.src;
                link.classList.add('image-link');
                link.setAttribute('target', '_blank');
                link.setAttribute('rel', 'noopener noreferrer');
                
                // Replace image with linked image
                img.parentNode.insertBefore(link, img);
                link.appendChild(img);
            }
        });
    });
} 