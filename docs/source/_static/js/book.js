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
        // Always set light theme as default
        document.documentElement.classList.remove('dark-theme');
        localStorage.setItem('theme', 'light');
        
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

    // Expand all sections in the sidebar
    expandAllSections();
    
    // Add chapter numbers to headings
    addChapterNumbers();
    
    // Make figures and tables more book-like
    enhanceFiguresAndTables();
    
    // Add page-turn effect when navigating
    setupPageTurnEffect();

    // Initialize all features
    setupReadingProgress();
    setupChapterNavigation();
    setupSectionHighlighting();
    setupSmoothScrolling();
    setupMobileNavigation();
    setupDarkMode();
    setupPrintOptimization();

    // Enhance special content
    enhanceSpecialContent();
    addBookFormatting();
    setupPageNavigation();
});

/**
 * Expands all navigation sections in the sidebar
 */
function expandAllSections() {
    // Expand all top level items
    document.querySelectorAll('.wy-menu-vertical li.toctree-l1').forEach(item => {
        item.classList.add('current');
        
        // Show all immediate child <ul> elements
        const submenu = item.querySelector('ul');
        if (submenu) {
            submenu.style.display = 'block';
            
            // And then all their children's <ul> elements, etc.
            submenu.querySelectorAll('li').forEach(nestedItem => {
                nestedItem.classList.add('current');
                const nestedSubmenu = nestedItem.querySelector('ul');
                if (nestedSubmenu) {
                    nestedSubmenu.style.display = 'block';
                }
            });
        }
    });
}

/**
 * Adds chapter numbers to headings for book-like structure
 */
function addChapterNumbers() {
    // Only add to top-level content h1s that are in the main content
    const mainContent = document.querySelector('.wy-nav-content');
    if (!mainContent) return;
    
    const h1Elements = mainContent.querySelectorAll('h1');
    
    // Don't add chapter numbers if there's only one h1
    if (h1Elements.length <= 1) return;
    
    h1Elements.forEach(function(h1, index) {
        // Skip the title page
        if (index === 0 && h1.textContent.includes('memories-dev')) return;
        
        // Create chapter number element
        const chapterNum = document.createElement('span');
        chapterNum.className = 'chapter-number';
        chapterNum.textContent = 'Chapter ' + index;
        
        // Insert before the heading text
        h1.insertBefore(chapterNum, h1.firstChild);
    });
}

/**
 * Makes figures and tables more book-like
 */
function enhanceFiguresAndTables() {
    // Add styling to figures
    const figures = document.querySelectorAll('.figure');
    figures.forEach(function(figure, index) {
        // Add figure number
        const caption = figure.querySelector('.caption');
        if (caption) {
            caption.innerHTML = '<span class="figure-number">Figure ' + (index + 1) + ':</span> ' + caption.innerHTML;
        }
    });
    
    // Add styling to tables
    const tables = document.querySelectorAll('table.docutils');
    tables.forEach(function(table, index) {
        // Find caption or create one
        let caption = table.previousElementSibling;
        if (caption && !caption.classList.contains('table-caption')) {
            // Create new caption
            caption = document.createElement('p');
            caption.className = 'table-caption';
            caption.innerHTML = '<span class="table-number">Table ' + (index + 1) + '</span>';
            table.parentNode.insertBefore(caption, table);
        }
    });
}

/**
 * Sets up a page turn effect when navigating between pages
 */
function setupPageTurnEffect() {
    // Add click handler to navigation links
    const links = document.querySelectorAll('a[href^=""]');
    links.forEach(function(link) {
        link.addEventListener('click', function(e) {
            // Don't apply to external links
            if (link.href.includes('#') || link.getAttribute('target') === '_blank') return;
            
            // Create page turn effect
            const content = document.querySelector('.wy-nav-content');
            if (content) {
                content.classList.add('page-turn');
                
                // Reset after transition
                setTimeout(function() {
                    content.classList.remove('page-turn');
                }, 500);
            }
        });
    });
    
    // Add the CSS for the effect if not already present
    if (!document.getElementById('page-turn-style')) {
        const style = document.createElement('style');
        style.id = 'page-turn-style';
        style.textContent = `
            @keyframes pageTurn {
                0% { opacity: 1; transform: translateX(0); }
                20% { opacity: 0.8; transform: translateX(10px); }
                100% { opacity: 0; transform: translateX(30px); }
            }
            .page-turn {
                animation: pageTurn 0.3s ease-in-out forwards;
            }
        `;
        document.head.appendChild(style);
    }
}

/**
 * Enhance the rendering of special content like mermaid diagrams and math formulas
 */
function enhanceSpecialContent() {
    // Handle mermaid diagrams
    if (typeof mermaid !== 'undefined') {
        try {
            // Configure mermaid with book-appropriate theme
            mermaid.initialize({
                startOnLoad: true,
                theme: 'neutral',
                securityLevel: 'loose',
                flowchart: {
                    useMaxWidth: true,
                    htmlLabels: true,
                    curve: 'basis'
                },
                fontFamily: '"Palatino Linotype", "Book Antiqua", Palatino, serif'
            });
            
            // Force render any mermaid diagrams
            setTimeout(function() {
                try {
                    mermaid.init(undefined, document.querySelectorAll('.mermaid:not([data-processed="true"])'));
                    console.log('Mermaid diagrams rendered successfully');
                } catch (err) {
                    console.error('Error rendering mermaid diagrams:', err);
                }
            }, 1000);
        } catch (err) {
            console.error('Error initializing mermaid:', err);
        }
    } else {
        console.log('Mermaid library not loaded, diagrams might not render correctly');
        
        // Try to load mermaid dynamically
        var script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js';
        script.onload = function() {
            console.log('Mermaid loaded dynamically');
            if (typeof mermaid !== 'undefined') {
                mermaid.initialize({
                    startOnLoad: true,
                    theme: 'neutral'
                });
                setTimeout(function() {
                    mermaid.init(undefined, document.querySelectorAll('.mermaid'));
                }, 500);
            }
        };
        document.head.appendChild(script);
    }
    
    // Handle math rendering
    document.querySelectorAll('.math').forEach(function(mathElement) {
        // Add special styling for math blocks
        mathElement.classList.add('math-rendered');
        
        // For block math, add a centered container
        if (!mathElement.classList.contains('inline')) {
            if (!mathElement.parentNode.classList.contains('math-wrapper')) {
                const wrapper = document.createElement('div');
                wrapper.className = 'math-wrapper';
                mathElement.parentNode.insertBefore(wrapper, mathElement);
                wrapper.appendChild(mathElement);
            }
        }
    });
    
    // Monitor for new content (for dynamic pages)
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                // Check for new mermaid diagrams
                if (typeof mermaid !== 'undefined') {
                    const newMermaidDiagrams = document.querySelectorAll('.mermaid:not([data-processed="true"])');
                    if (newMermaidDiagrams.length > 0) {
                        try {
                            mermaid.init(undefined, newMermaidDiagrams);
                        } catch (err) {
                            console.error('Error rendering new mermaid diagrams:', err);
                        }
                    }
                }
                
                // Check for new math elements
                const newMathElements = document.querySelectorAll('.math:not(.math-rendered)');
                newMathElements.forEach(function(mathElement) {
                    mathElement.classList.add('math-rendered');
                    if (!mathElement.classList.contains('inline') && 
                        !mathElement.parentNode.classList.contains('math-wrapper')) {
                        const wrapper = document.createElement('div');
                        wrapper.className = 'math-wrapper';
                        mathElement.parentNode.insertBefore(wrapper, mathElement);
                        wrapper.appendChild(mathElement);
                    }
                });
            }
        });
    });
    
    observer.observe(document.body, { childList: true, subtree: true });
}

/**
 * Add chapter numbering to headings for book-like structure
 */
function addBookFormatting() {
    // Add chapter numbers
    const mainContent = document.querySelector('.wy-nav-content');
    if (!mainContent) return;
    
    // Get all top-level headings
    const headings = mainContent.querySelectorAll('h1');
    
    // Skip the title page if it exists
    const startIndex = document.querySelector('.wy-nav-content > h1') ? 1 : 0;
    
    // Add chapter numbering
    headings.forEach((heading, index) => {
        if (index >= startIndex) {
            const chapterNum = index - startIndex + 1;
            
            // Create chapter label
            const chapterLabel = document.createElement('div');
            chapterLabel.className = 'chapter-label';
            chapterLabel.innerHTML = `Chapter ${chapterNum}`;
            
            // Insert before heading
            heading.parentNode.insertBefore(chapterLabel, heading);
            
            // Add chapter class to section
            heading.closest('div').classList.add('chapter-section');
        }
    });
    
    // Add decorative elements to sections
    document.querySelectorAll('.section').forEach(section => {
        // Add decorative line at end of sections
        const decorativeLine = document.createElement('div');
        decorativeLine.className = 'decorative-line';
        section.appendChild(decorativeLine);
    });
}

/**
 * Add page-like navigation
 */
function setupPageNavigation() {
    // Add page turn effect to next/prev buttons
    const nextButton = document.querySelector('.btn-neutral.float-right');
    const prevButton = document.querySelector('.btn-neutral.float-left');
    
    if (nextButton) {
        nextButton.innerHTML = nextButton.innerHTML.replace('Next', 'Next Page →');
        nextButton.classList.add('page-turn', 'next-page');
        
        nextButton.addEventListener('click', function(e) {
            // Skip if modifier keys are pressed (new tab, etc.)
            if (e.ctrlKey || e.shiftKey || e.metaKey) return;
            
            e.preventDefault();
            document.body.classList.add('page-turning-forward');
            
            setTimeout(function() {
                window.location.href = nextButton.getAttribute('href');
            }, 400);
        });
    }
    
    if (prevButton) {
        prevButton.innerHTML = prevButton.innerHTML.replace('Previous', '← Previous Page');
        prevButton.classList.add('page-turn', 'prev-page');
        
        prevButton.addEventListener('click', function(e) {
            // Skip if modifier keys are pressed (new tab, etc.)
            if (e.ctrlKey || e.shiftKey || e.metaKey) return;
            
            e.preventDefault();
            document.body.classList.add('page-turning-backward');
            
            setTimeout(function() {
                window.location.href = prevButton.getAttribute('href');
            }, 400);
        });
    }
} 