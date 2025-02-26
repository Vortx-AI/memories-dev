/**
 * Lazy Image Loader for Memories-Dev Documentation
 * 
 * This script implements lazy loading for images to improve page load performance.
 * Images with the 'lazy-load' class will only be loaded when they scroll into view.
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get all images with lazy-load class
    const lazyImages = [].slice.call(document.querySelectorAll('img.lazy-load'));
    
    if ('IntersectionObserver' in window) {
        // Use Intersection Observer API for modern browsers
        let lazyImageObserver = new IntersectionObserver(function(entries, observer) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    let lazyImage = entry.target;
                    if (lazyImage.dataset.src) {
                        lazyImage.src = lazyImage.dataset.src;
                        lazyImage.removeAttribute('data-src');
                        lazyImage.classList.add('loaded');
                        lazyImageObserver.unobserve(lazyImage);
                    }
                }
            });
        });

        lazyImages.forEach(function(lazyImage) {
            lazyImageObserver.observe(lazyImage);
        });
    } else {
        // Fallback for browsers without Intersection Observer support
        let active = false;

        const lazyLoad = function() {
            if (active === false) {
                active = true;

                setTimeout(function() {
                    lazyImages.forEach(function(lazyImage) {
                        if ((lazyImage.getBoundingClientRect().top <= window.innerHeight && 
                             lazyImage.getBoundingClientRect().bottom >= 0) &&
                            getComputedStyle(lazyImage).display !== 'none') {
                            
                            if (lazyImage.dataset.src) {
                                lazyImage.src = lazyImage.dataset.src;
                                lazyImage.removeAttribute('data-src');
                                lazyImage.classList.add('loaded');
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

        // Add event listeners for fallback lazy loading
        document.addEventListener('scroll', lazyLoad);
        window.addEventListener('resize', lazyLoad);
        window.addEventListener('orientationchange', lazyLoad);
        
        // Initial load check
        lazyLoad();
    }
});
