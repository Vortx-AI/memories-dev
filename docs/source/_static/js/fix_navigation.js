// Enhanced navigation fix for memories-dev documentation

document.addEventListener('DOMContentLoaded', function() {
    // Remove all book experience elements
    removeBookExperience();
    
    // Fix navigation links and expand current section
    fixNavigation();
    
    // Add helpful ReadTheDocs elements
    addReadTheDocsElements();
    
    // Add code features
    enhanceCodeBlocks();
    
    // Fix broken links in documentation
    fixBrokenLinks();
    
    // Add dark/light mode toggle if not present
    addThemeToggle();
    
    // Add scroll to top button
    addScrollToTopButton();
});

/**
 * Remove all elements from the book experience that might interfere with navigation
 */
function removeBookExperience() {
    const elementsToRemove = [
        '.book-container', '.book-cover-container', '.book-front', 
        '.book-side', '.book-spine', '.book-cover-3d', '.book-decoration', 
        '.journey-map', '.page-turning', '.page-loaded', '.book-cover', 
        '.book-navigation', '.book-progress-container', '.journey-buttons', 
        '.book-intro', '.floating-toc', '.floating-toc-button', '.book-quote', 
        '.book-footer', '.earth-banner', '.earth-visualization', 
        '.atmosphere', '.clouds', '.grid'
    ];
    
    elementsToRemove.forEach(selector => {
        document.querySelectorAll(selector).forEach(element => {
            element.style.display = 'none';
        });
    });
}

/**
 * Fix navigation and ensure all links work properly
 */
function fixNavigation() {
    // Make sure the navigation panel is visible
    const navSide = document.querySelector('.wy-nav-side');
    if (navSide) {
        navSide.style.display = 'block';
        navSide.style.visibility = 'visible';
    }
    
    // Ensure content wrapping is correct
    const contentWrap = document.querySelector('.wy-nav-content-wrap');
    if (contentWrap) {
        contentWrap.style.marginLeft = window.innerWidth > 768 ? '300px' : '0';
    }
    
    // Add mobile navigation toggle
    if (!document.querySelector('.mobile-nav-toggle')) {
        const toggle = document.createElement('button');
        toggle.className = 'mobile-nav-toggle';
        toggle.innerHTML = '☰';
        toggle.setAttribute('aria-label', 'Toggle navigation menu');
        
        document.body.appendChild(toggle);
        
        toggle.addEventListener('click', () => {
            document.body.classList.toggle('nav-open');
            if (navSide) {
                navSide.classList.toggle('shift');
            }
            if (contentWrap) {
                contentWrap.classList.toggle('shift');
            }
        });
    }
    
    // Fix all navigation links
    const navLinks = document.querySelectorAll('.wy-menu-vertical a');
    navLinks.forEach(link => {
        // Clone to remove any existing event listeners
        const oldLink = link.cloneNode(true);
        link.parentNode.replaceChild(oldLink, link);
        
        // Make sure it opens in the same tab/window
        oldLink.setAttribute('target', '_self');
    });
    
    // Expand current section and its parents
    const currentItems = document.querySelectorAll('.wy-menu-vertical li.current');
    currentItems.forEach(item => {
        // Show the submenu
        const submenu = item.querySelector('ul');
        if (submenu) {
            submenu.style.display = 'block';
        }
        
        // Also expand parent sections
        let parent = item.parentNode;
        while (parent && parent.tagName === 'UL') {
            parent.style.display = 'block';
            parent = parent.parentNode && parent.parentNode.parentNode;
        }
    });
}

/**
 * Add helpful elements from ReadTheDocs theme
 */
function addReadTheDocsElements() {
    // Add version selector if not present
    const sideNav = document.querySelector('.wy-side-nav-search');
    if (sideNav && !document.querySelector('.version-selector')) {
        const version = document.querySelector('.version');
        if (version) {
            const versionText = version.textContent.trim();
            const versionSelector = document.createElement('div');
            versionSelector.className = 'version-selector';
            versionSelector.innerHTML = `
                <select id="version-selector">
                    <option value="${versionText}" selected>${versionText}</option>
                    <option value="latest">latest</option>
                    <option value="stable">stable</option>
                </select>
            `;
            sideNav.appendChild(versionSelector);
            
            // Add event listener
            document.getElementById('version-selector').addEventListener('change', function() {
                const selectedVersion = this.value;
                if (selectedVersion !== versionText) {
                    const currentPath = window.location.pathname;
                    const newPath = currentPath.replace(/\/\d+\.\d+\.\d+\//, `/${selectedVersion}/`);
                    window.location.href = newPath;
                }
            });
        }
    }
    
    // Add 'On This Page' sidebar if not present
    const contentContainer = document.querySelector('.wy-nav-content');
    if (contentContainer && !document.querySelector('.local-toc')) {
        const headings = contentContainer.querySelectorAll('h2, h3');
        if (headings.length > 0) {
            const tocContainer = document.createElement('div');
            tocContainer.className = 'local-toc';
            
            let tocHTML = '<div class="local-toc-title">On This Page</div><ul>';
            headings.forEach(heading => {
                const id = heading.id;
                const text = heading.textContent;
                const level = heading.tagName === 'H2' ? 'local-toc-level-1' : 'local-toc-level-2';
                
                if (id && text) {
                    tocHTML += `<li class="${level}"><a href="#${id}">${text}</a></li>`;
                }
            });
            tocHTML += '</ul>';
            
            tocContainer.innerHTML = tocHTML;
            contentContainer.insertBefore(tocContainer, contentContainer.firstChild);
            
            // Add styles
            const style = document.createElement('style');
            style.textContent = `
                .local-toc {
                    background-color: #f8f9fa;
                    border: 1px solid #e3e3e3;
                    border-radius: 4px;
                    padding: 15px;
                    margin-bottom: 24px;
                }
                
                .local-toc-title {
                    font-weight: bold;
                    margin-bottom: 10px;
                }
                
                .local-toc ul {
                    margin: 0;
                    padding: 0;
                    list-style-type: none;
                }
                
                .local-toc-level-1 {
                    margin-top: 8px;
                }
                
                .local-toc-level-2 {
                    padding-left: 15px;
                    margin-top: 5px;
                }
                
                .local-toc a {
                    text-decoration: none;
                }
                
                @media (max-width: 768px) {
                    .local-toc {
                        display: none;
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }
}

/**
 * Enhance code blocks with copy buttons
 */
function enhanceCodeBlocks() {
    const codeBlocks = document.querySelectorAll('div[class^="highlight"]');
    
    codeBlocks.forEach(block => {
        if (!block.querySelector('.copy-button')) {
            const copyButton = document.createElement('button');
            copyButton.className = 'copy-button';
            copyButton.textContent = 'Copy';
            copyButton.title = 'Copy to clipboard';
            
            copyButton.addEventListener('click', () => {
                const code = block.querySelector('pre').textContent;
                navigator.clipboard.writeText(code).then(() => {
                    copyButton.textContent = 'Copied!';
                    setTimeout(() => {
                        copyButton.textContent = 'Copy';
                    }, 2000);
                });
            });
            
            block.appendChild(copyButton);
        }
    });
    
    // Add styles if not present
    if (!document.querySelector('style#code-styles')) {
        const style = document.createElement('style');
        style.id = 'code-styles';
        style.textContent = `
            div[class^="highlight"] {
                position: relative;
            }
            
            .copy-button {
                position: absolute;
                top: 5px;
                right: 5px;
                background: rgba(0, 0, 0, 0.2);
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
                cursor: pointer;
                opacity: 0.6;
                transition: opacity 0.2s;
            }
            
            .copy-button:hover {
                opacity: 1;
            }
            
            div[class^="highlight"]:hover .copy-button {
                opacity: 0.8;
            }
        `;
        document.head.appendChild(style);
    }
}

/**
 * Fix broken links in the documentation
 */
function fixBrokenLinks() {
    // Replace any broken links with correct paths
    const links = document.querySelectorAll('a[href]');
    links.forEach(link => {
        const href = link.getAttribute('href');
        
        // Fix incorrect references to non-existent pages
        if (href.includes('unknown document')) {
            link.style.color = '#999';
            link.style.textDecoration = 'line-through';
            link.title = 'This link points to a missing document';
        }
        
        // Fix bookmarks related links
        if (href.includes('/bookmarks/')) {
            // For demonstration - replace with actual bookmarks URL
            link.setAttribute('href', '/bookmarks.html');
        }
    });
}

/**
 * Add theme toggle button
 */
function addThemeToggle() {
    if (!document.querySelector('#theme-toggle')) {
        const navSearch = document.querySelector('.wy-side-nav-search');
        if (navSearch) {
            const toggleButton = document.createElement('button');
            toggleButton.id = 'theme-toggle';
            toggleButton.className = 'theme-toggle';
            toggleButton.innerHTML = '🌓';
            toggleButton.title = 'Toggle dark/light mode';
            
            navSearch.appendChild(toggleButton);
            
            // Add toggle functionality
            toggleButton.addEventListener('click', function() {
                document.documentElement.classList.toggle('dark-theme');
                const isDark = document.documentElement.classList.contains('dark-theme');
                localStorage.setItem('theme', isDark ? 'dark' : 'light');
            });
            
            // Set initial theme
            const savedTheme = localStorage.getItem('theme');
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            
            if ((savedTheme === 'dark') || (!savedTheme && prefersDark)) {
                document.documentElement.classList.add('dark-theme');
            }
            
            // Add styles
            const style = document.createElement('style');
            style.textContent = `
                .theme-toggle {
                    position: absolute;
                    top: 12px;
                    right: 12px;
                    width: 30px;
                    height: 30px;
                    border-radius: 50%;
                    background: rgba(0, 0, 0, 0.1);
                    border: none;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 16px;
                    transition: background 0.2s;
                    z-index: 20;
                }
                
                .theme-toggle:hover {
                    background: rgba(0, 0, 0, 0.2);
                }
            `;
            document.head.appendChild(style);
        }
    }
}

/**
 * Add scroll to top button
 */
function addScrollToTopButton() {
    if (!document.querySelector('.back-to-top')) {
        const backToTop = document.createElement('button');
        backToTop.className = 'back-to-top';
        backToTop.innerHTML = '&uarr;';
        backToTop.title = 'Back to top';
        
        document.body.appendChild(backToTop);
        
        // Add functionality
        backToTop.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
        
        // Show/hide based on scroll position
        window.addEventListener('scroll', () => {
            if (window.scrollY > 300) {
                backToTop.classList.add('visible');
            } else {
                backToTop.classList.remove('visible');
            }
        });
        
        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .back-to-top {
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: var(--primary-color, #2b6cb0);
                color: white;
                border: none;
                font-size: 20px;
                cursor: pointer;
                opacity: 0;
                transition: opacity 0.3s;
                z-index: 100;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
            }
            
            .back-to-top.visible {
                opacity: 0.7;
            }
            
            .back-to-top:hover {
                opacity: 1;
            }
        `;
        document.head.appendChild(style);
    }
}

// Add responsive styles
const style = document.createElement('style');
style.textContent = `
    .mobile-nav-toggle {
        display: none;
        position: fixed;
        top: 1rem;
        left: 1rem;
        z-index: 300;
        background: var(--primary-color);
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem;
        font-size: 1.5rem;
        cursor: pointer;
    }
    
    @media screen and (max-width: 768px) {
        .mobile-nav-toggle {
            display: block;
        }
        
        body.nav-open .wy-nav-content-wrap {
            transform: translateX(300px);
        }
        
        .wy-nav-content-wrap {
            transition: transform 0.3s ease;
        }
    }
`;
document.head.appendChild(style); 