/**
 * Book.js - Essential functionality for book-like documentation
 */

document.addEventListener('DOMContentLoaded', function() {
    // Reading Progress
    function setupReadingProgress() {
        const progress = document.createElement('div');
        progress.className = 'reading-progress';
        document.body.appendChild(progress);

        function updateProgress() {
            const docHeight = document.documentElement.scrollHeight - window.innerHeight;
            const scrollPos = window.scrollY;
            const percentage = (scrollPos / docHeight) * 100;
            progress.style.width = `${percentage}%`;
        }

        window.addEventListener('scroll', updateProgress);
        updateProgress();
    }

    // Chapter Navigation
    function setupChapterNavigation() {
        const content = document.querySelector('.wy-nav-content');
        if (!content) return;

        const nav = document.createElement('nav');
        nav.className = 'chapter-nav';
        
        const prevLink = document.querySelector('link[rel="prev"]');
        const nextLink = document.querySelector('link[rel="next"]');

        if (prevLink) {
            const prev = document.createElement('a');
            prev.href = prevLink.href;
            prev.className = 'prev-chapter';
            prev.textContent = 'Previous Chapter';
            nav.appendChild(prev);
        }

        if (nextLink) {
            const next = document.createElement('a');
            next.href = nextLink.href;
            next.className = 'next-chapter';
            next.textContent = 'Next Chapter';
            nav.appendChild(next);
        }

        if (prevLink || nextLink) {
            content.appendChild(nav);
        }
    }

    // Section Highlighting
    function setupSectionHighlighting() {
        const sections = document.querySelectorAll('section[id]');
        const menu = document.querySelector('.wy-menu-vertical');
        
        if (!menu || !sections.length) return;

        function highlightSection() {
            const scrollPos = window.scrollY + 100;
            
            for (const section of sections) {
                if (section.offsetTop <= scrollPos && 
                    section.offsetTop + section.offsetHeight > scrollPos) {
                    const link = menu.querySelector(`a[href="#${section.id}"]`);
                    if (link) {
                        menu.querySelectorAll('a').forEach(a => a.classList.remove('current'));
                        link.classList.add('current');
                    }
                    break;
                }
            }
        }

        window.addEventListener('scroll', highlightSection);
        highlightSection();
    }

    // Smooth Scrolling
    function setupSmoothScrolling() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    // Mobile Navigation
    function setupMobileNavigation() {
        const menuButton = document.querySelector('.wy-nav-top button');
        if (!menuButton) return;

        menuButton.addEventListener('click', function() {
            document.querySelector('.wy-nav-side').classList.toggle('shift');
        });
    }

    // Dark Mode
    function setupDarkMode() {
        // Explicitly set light theme as default
        document.documentElement.classList.remove('dark-theme');
        
        // Check for saved theme preference
        const savedTheme = localStorage.getItem('theme');
        
        // Apply saved theme if it exists
        if (savedTheme === 'dark') {
            document.documentElement.classList.add('dark-theme');
        } else {
            // Ensure light theme is active (default)
            document.documentElement.classList.remove('dark-theme');
            // Set light theme in localStorage if not already set
            if (!savedTheme) {
                localStorage.setItem('theme', 'light');
            }
        }
        
        // Listen for theme toggle events
        document.addEventListener('themeToggled', function(e) {
            if (e.detail.theme === 'dark') {
                document.documentElement.classList.add('dark-theme');
            } else {
                document.documentElement.classList.remove('dark-theme');
            }
            
            // Update Mermaid diagrams if they exist
            if (window.mermaid) {
                document.dispatchEvent(new Event('mermaidThemeUpdate'));
            }
        });
    }

    // Print Optimization
    function setupPrintOptimization() {
        if (!window.matchMedia) return;
        
        const mediaQueryList = window.matchMedia('print');
        mediaQueryList.addListener(function(mql) {
            if (mql.matches) {
                document.querySelectorAll('.wy-nav-side').forEach(el => {
                    el.style.display = 'none';
                });
            }
        });
    }

    // Initialize all features
    setupReadingProgress();
    setupChapterNavigation();
    setupSectionHighlighting();
    setupSmoothScrolling();
    setupMobileNavigation();
    setupDarkMode();
    setupPrintOptimization();
}); 