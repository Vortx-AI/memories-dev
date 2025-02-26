// Professional Developer Theme JavaScript for memories-dev documentation

document.addEventListener('DOMContentLoaded', function() {
    // Add copy buttons to code blocks
    addCopyButtons();
    
    // Add language indicators to code blocks
    addLanguageIndicators();
    
    // Enhance navigation experience
    enhanceNavigation();
    
    // Improve search functionality
    improveSearch();
    
    // Add responsive behavior
    addResponsiveBehavior();
    
    // Add table of contents highlighting
    addTocHighlighting();
    
    // Add smooth scrolling for all anchor links
    addSmoothScrollingToAnchors();
    
    // Add keyboard navigation shortcuts
    addKeyboardShortcuts();
    
    // Fix any RTD theme specific issues
    fixRtdThemeIssues();
});

/**
 * Add copy buttons to code blocks
 */
function addCopyButtons() {
    // Find all code blocks
    const codeBlocks = document.querySelectorAll('div.highlight');
    
    codeBlocks.forEach(function(codeBlock) {
        // Skip if already has a copy button
        if (codeBlock.querySelector('.copybtn')) {
            return;
        }
        
        // Create copy button
        const button = document.createElement('button');
        button.className = 'copybtn';
        button.title = 'Copy to clipboard';
        button.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M4 1.5H3a2 2 0 0 0-2 2V14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V3.5a2 2 0 0 0-2-2h-1v1h1a1 1 0 0 1 1 1V14a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V3.5a1 1 0 0 1 1-1h1v-1z"/><path d="M9.5 1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5h3zm-3-1A1.5 1.5 0 0 0 5 1.5v1A1.5 1.5 0 0 0 6.5 4h3A1.5 1.5 0 0 0 11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3z"/></svg>';
        
        // Add click event
        button.addEventListener('click', function() {
            // Get the code content
            const code = codeBlock.querySelector('pre').textContent;
            
            // Copy to clipboard
            navigator.clipboard.writeText(code).then(function() {
                // Visual feedback
                button.classList.add('copied');
                button.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg>';
                
                // Reset after 2 seconds
                setTimeout(function() {
                    button.classList.remove('copied');
                    button.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M4 1.5H3a2 2 0 0 0-2 2V14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V3.5a2 2 0 0 0-2-2h-1v1h1a1 1 0 0 1 1 1V14a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V3.5a1 1 0 0 1 1-1h1v-1z"/><path d="M9.5 1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5h3zm-3-1A1.5 1.5 0 0 0 5 1.5v1A1.5 1.5 0 0 0 6.5 4h3A1.5 1.5 0 0 0 11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3z"/></svg>';
                }, 2000);
            }).catch(function(error) {
                console.error('Could not copy text: ', error);
            });
        });
        
        // Add button to code block
        codeBlock.appendChild(button);
    });
}

/**
 * Add language indicators to code blocks
 */
function addLanguageIndicators() {
    // Find all code blocks
    const codeBlocks = document.querySelectorAll('div.highlight');
    
    codeBlocks.forEach(function(codeBlock) {
        // Skip if already has a language indicator
        if (codeBlock.querySelector('.lang-indicator')) {
            return;
        }
        
        // Try to determine the language
        let language = 'code';
        
        // Check for language classes
        const classes = codeBlock.className.split(' ');
        for (let i = 0; i < classes.length; i++) {
            if (classes[i].startsWith('language-')) {
                language = classes[i].replace('language-', '');
                break;
            }
        }
        
        // Check parent element for language classes
        if (language === 'code' && codeBlock.parentElement) {
            const parentClasses = codeBlock.parentElement.className.split(' ');
            for (let i = 0; i < parentClasses.length; i++) {
                if (parentClasses[i].startsWith('language-')) {
                    language = parentClasses[i].replace('language-', '');
                    break;
                }
            }
        }
        
        // Create language indicator
        const indicator = document.createElement('div');
        indicator.className = 'lang-indicator';
        indicator.textContent = language;
        
        // Add indicator to code block
        codeBlock.appendChild(indicator);
    });
}

/**
 * Enhance navigation experience
 */
function enhanceNavigation() {
    // Highlight current page in navigation
    highlightCurrentPage();
    
    // Add smooth scrolling to anchor links
    addSmoothScrolling();
    
    // Expand navigation sections for current page
    expandCurrentSection();
    
    // Add section navigation
    addSectionNavigation();
}

/**
 * Highlight the current page in navigation
 */
function highlightCurrentPage() {
    // Get current page URL
    const currentUrl = window.location.pathname;
    
    // Find all navigation links
    const navLinks = document.querySelectorAll('.wy-menu-vertical a');
    
    navLinks.forEach(function(link) {
        // Check if link href matches current URL
        if (link.href.includes(currentUrl)) {
            link.classList.add('current');
            
            // Also highlight parent list items
            let parent = link.parentElement;
            while (parent && parent.tagName !== 'NAV') {
                if (parent.tagName === 'LI') {
                    parent.classList.add('current-parent');
                }
                parent = parent.parentElement;
            }
        }
    });
}

/**
 * Add smooth scrolling to anchor links
 */
function addSmoothScrolling() {
    // Find all anchor links within the content
    const anchorLinks = document.querySelectorAll('.wy-nav-content a[href^="#"]');
    
    anchorLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            // Get the target element
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                // Prevent default behavior
                e.preventDefault();
                
                // Scroll smoothly to target
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
                
                // Update URL
                history.pushState(null, null, `#${targetId}`);
            }
        });
    });
}

/**
 * Add smooth scrolling to all anchor links
 */
function addSmoothScrollingToAnchors() {
    // Find all anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                e.preventDefault();
                
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
                
                // Update URL
                history.pushState(null, null, `#${targetId}`);
            }
        });
    });
}

/**
 * Expand navigation sections for current page
 */
function expandCurrentSection() {
    // Find current page in navigation
    const currentLinks = document.querySelectorAll('.wy-menu-vertical a.current');
    
    currentLinks.forEach(function(link) {
        // Find parent list items with ul children
        let parent = link.parentElement;
        while (parent && !parent.classList.contains('wy-menu-vertical')) {
            if (parent.tagName === 'LI') {
                const ul = parent.querySelector('ul');
                if (ul) {
                    ul.style.display = 'block';
                    parent.classList.add('current');
                }
            }
            parent = parent.parentElement;
        }
    });
}

/**
 * Add section navigation
 */
function addSectionNavigation() {
    // Get the main content area
    const content = document.querySelector('.wy-nav-content');
    
    if (!content) return;
    
    // Find all headings in the content
    const headings = content.querySelectorAll('h2, h3');
    
    if (headings.length < 3) return; // Not enough headings to warrant section navigation
    
    // Create section navigation container
    const sectionNav = document.createElement('div');
    sectionNav.className = 'section-nav';
    sectionNav.innerHTML = '<h4>On This Page</h4><ul></ul>';
    
    // Add headings to section navigation
    const sectionNavList = sectionNav.querySelector('ul');
    
    headings.forEach(function(heading) {
        // Create ID for heading if it doesn't have one
        if (!heading.id) {
            heading.id = heading.textContent.toLowerCase().replace(/[^a-z0-9]+/g, '-');
        }
        
        // Create list item
        const li = document.createElement('li');
        li.className = heading.tagName.toLowerCase();
        
        // Create link
        const a = document.createElement('a');
        a.href = `#${heading.id}`;
        a.textContent = heading.textContent;
        
        // Add link to list item
        li.appendChild(a);
        
        // Add list item to section navigation
        sectionNavList.appendChild(li);
    });
    
    // Add section navigation to content
    const contentFirstHeading = content.querySelector('h1');
    if (contentFirstHeading) {
        contentFirstHeading.parentNode.insertBefore(sectionNav, contentFirstHeading.nextSibling);
    } else {
        content.insertBefore(sectionNav, content.firstChild);
    }
    
    // Add styles for section navigation
    const style = document.createElement('style');
    style.textContent = `
        .section-nav {
            background-color: rgba(66, 133, 244, 0.05);
            border-radius: 4px;
            padding: 1em;
            margin: 1.5em 0;
            border-left: 4px solid rgba(66, 133, 244, 0.3);
        }
        
        .section-nav h4 {
            margin-top: 0;
            margin-bottom: 0.5em;
            color: var(--accent-color);
            font-size: 1.1em;
        }
        
        .section-nav ul {
            list-style-type: none;
            padding-left: 0;
            margin-bottom: 0;
        }
        
        .section-nav li {
            margin-bottom: 0.3em;
        }
        
        .section-nav li.h3 {
            padding-left: 1em;
            font-size: 0.9em;
        }
        
        .section-nav a {
            color: var(--accent-color);
            text-decoration: none;
        }
        
        .section-nav a:hover {
            text-decoration: underline;
        }
        
        @media (min-width: 992px) {
            .section-nav {
                position: sticky;
                top: 1.5em;
                max-height: calc(100vh - 3em);
                overflow-y: auto;
            }
        }
    `;
    
    document.head.appendChild(style);
}

/**
 * Improve search functionality
 */
function improveSearch() {
    // Get search input
    const searchInput = document.querySelector('input[name="q"]');
    
    if (searchInput) {
        // Add placeholder
        searchInput.setAttribute('placeholder', 'Search documentation...');
        
        // Add clear button
        const clearButton = document.createElement('button');
        clearButton.className = 'search-clear';
        clearButton.innerHTML = '&times;';
        clearButton.style.display = 'none';
        clearButton.setAttribute('type', 'button');
        clearButton.setAttribute('aria-label', 'Clear search');
        
        // Style the clear button
        clearButton.style.position = 'absolute';
        clearButton.style.right = '10px';
        clearButton.style.top = '50%';
        clearButton.style.transform = 'translateY(-50%)';
        clearButton.style.background = 'none';
        clearButton.style.border = 'none';
        clearButton.style.color = 'var(--text-muted)';
        clearButton.style.fontSize = '1.2em';
        clearButton.style.cursor = 'pointer';
        
        // Add clear button after search input
        searchInput.parentNode.style.position = 'relative';
        searchInput.parentNode.appendChild(clearButton);
        
        // Show/hide clear button based on input content
        searchInput.addEventListener('input', function() {
            clearButton.style.display = this.value ? 'block' : 'none';
        });
        
        // Clear search input when button is clicked
        clearButton.addEventListener('click', function() {
            searchInput.value = '';
            this.style.display = 'none';
            searchInput.focus();
        });
    }
}

/**
 * Add responsive behavior
 */
function addResponsiveBehavior() {
    // Add toggle button for mobile navigation
    addMobileNavToggle();
    
    // Handle window resize events
    handleResize();
}

/**
 * Add toggle button for mobile navigation
 */
function addMobileNavToggle() {
    // Get sidebar
    const sidebar = document.querySelector('.wy-nav-side');
    
    if (sidebar) {
        // Create toggle button if it doesn't exist
        if (!document.querySelector('.mobile-nav-toggle')) {
            const toggleButton = document.createElement('button');
            toggleButton.className = 'mobile-nav-toggle';
            toggleButton.innerHTML = '<span></span><span></span><span></span>';
            toggleButton.setAttribute('aria-label', 'Toggle navigation');
            
            // Style the toggle button
            toggleButton.style.position = 'fixed';
            toggleButton.style.top = '1rem';
            toggleButton.style.left = '1rem';
            toggleButton.style.zIndex = '1000';
            toggleButton.style.display = 'none';
            toggleButton.style.flexDirection = 'column';
            toggleButton.style.justifyContent = 'space-between';
            toggleButton.style.width = '30px';
            toggleButton.style.height = '25px';
            toggleButton.style.background = 'none';
            toggleButton.style.border = 'none';
            toggleButton.style.cursor = 'pointer';
            toggleButton.style.padding = '0';
            
            // Style the toggle button spans
            const spans = toggleButton.querySelectorAll('span');
            spans.forEach(function(span) {
                span.style.display = 'block';
                span.style.width = '100%';
                span.style.height = '3px';
                span.style.background = 'var(--accent-color)';
                span.style.borderRadius = '2px';
                span.style.transition = 'all 0.3s ease-in-out';
            });
            
            // Add toggle button to document
            document.body.appendChild(toggleButton);
            
            // Add click event
            toggleButton.addEventListener('click', function() {
                sidebar.classList.toggle('shift');
                document.querySelector('.wy-nav-content-wrap').classList.toggle('shift');
                this.classList.toggle('active');
                
                // Transform toggle button to X when active
                if (this.classList.contains('active')) {
                    spans[0].style.transform = 'translateY(11px) rotate(45deg)';
                    spans[1].style.opacity = '0';
                    spans[2].style.transform = 'translateY(-11px) rotate(-45deg)';
                } else {
                    spans[0].style.transform = 'none';
                    spans[1].style.opacity = '1';
                    spans[2].style.transform = 'none';
                }
            });
        }
    }
}

/**
 * Handle window resize events
 */
function handleResize() {
    // Initial check
    checkWindowSize();
    
    // Add resize event listener
    window.addEventListener('resize', checkWindowSize);
}

/**
 * Check window size and adjust UI accordingly
 */
function checkWindowSize() {
    const toggleButton = document.querySelector('.mobile-nav-toggle');
    
    if (toggleButton) {
        if (window.innerWidth < 768) {
            toggleButton.style.display = 'flex';
        } else {
            toggleButton.style.display = 'none';
            
            // Reset mobile navigation
            const sidebar = document.querySelector('.wy-nav-side');
            if (sidebar) {
                sidebar.classList.remove('shift');
            }
            
            const contentWrap = document.querySelector('.wy-nav-content-wrap');
            if (contentWrap) {
                contentWrap.classList.remove('shift');
            }
            
            // Reset toggle button
            toggleButton.classList.remove('active');
            const spans = toggleButton.querySelectorAll('span');
            spans.forEach(function(span, index) {
                span.style.transform = 'none';
                span.style.opacity = '1';
            });
        }
    }
}

/**
 * Add table of contents highlighting
 */
function addTocHighlighting() {
    // Get all headings in the content
    const headings = document.querySelectorAll('.wy-nav-content h2, .wy-nav-content h3, .wy-nav-content h4');
    
    if (headings.length === 0) return;
    
    // Create IntersectionObserver
    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                // Get the corresponding TOC link
                const id = entry.target.getAttribute('id');
                if (!id) return;
                
                const tocLink = document.querySelector(`.section-nav a[href="#${id}"]`);
                if (!tocLink) return;
                
                if (entry.isIntersecting) {
                    // Remove active class from all links
                    document.querySelectorAll('.section-nav a').forEach((link) => {
                        link.classList.remove('active');
                    });
                    
                    // Add active class to current link
                    tocLink.classList.add('active');
                }
            });
        },
        {
            rootMargin: '-100px 0px -66%',
            threshold: 0
        }
    );
    
    // Observe all headings
    headings.forEach((heading) => {
        observer.observe(heading);
    });
    
    // Add styles for active TOC links
    const style = document.createElement('style');
    style.textContent = `
        .section-nav a.active {
            font-weight: bold;
            color: var(--accent-dark);
        }
    `;
    
    document.head.appendChild(style);
}

/**
 * Add keyboard shortcuts
 */
function addKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Only handle keyboard shortcuts when not in an input field
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }
        
        // / key for search
        if (e.key === '/' || (e.key === 'f' && (e.ctrlKey || e.metaKey))) {
            e.preventDefault();
            const searchInput = document.querySelector('input[name="q"]');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // ESC key to close search
        if (e.key === 'Escape') {
            const searchInput = document.querySelector('input[name="q"]');
            if (searchInput && document.activeElement === searchInput) {
                searchInput.blur();
            }
        }
    });
}

/**
 * Fix RTD theme specific issues
 */
function fixRtdThemeIssues() {
    // Fix table overflow
    const tables = document.querySelectorAll('.wy-nav-content table');
    tables.forEach(function(table) {
        const wrapper = document.createElement('div');
        wrapper.className = 'table-wrapper';
        wrapper.style.overflowX = 'auto';
        wrapper.style.marginBottom = '1.5em';
        
        table.parentNode.insertBefore(wrapper, table);
        wrapper.appendChild(table);
    });
    
    // Fix code block overflow
    const codeBlocks = document.querySelectorAll('.wy-nav-content pre');
    codeBlocks.forEach(function(codeBlock) {
        codeBlock.style.whiteSpace = 'pre';
        codeBlock.style.wordWrap = 'normal';
        codeBlock.style.overflowX = 'auto';
    });
} 