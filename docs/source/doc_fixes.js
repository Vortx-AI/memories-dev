/**
 * Documentation Fixes for Memories-Dev Documentation
 * 
 * This script fixes common issues and enhances the documentation usability:
 * 1. Fixes copy button positioning
 * 2. Adds anchor links to headings
 * 3. Enhances code block display
 * 4. Improves table responsiveness
 * 5. Fixes mobile layout issues
 * 6. Implements client-side search highlighting
 */
document.addEventListener('DOMContentLoaded', function() {
    // Fix copy button positioning
    fixCopyButtons();
    
    // Add anchor links to headings
    addAnchorLinks();
    
    // Enhance code blocks
    enhanceCodeBlocks();
    
    // Make tables responsive
    makeTablesResponsive();
    
    // Fix mobile layout issues
    fixMobileLayout();
    
    // Add search result highlighting
    enhanceSearch();
});

/**
 * Fix positioning of copy buttons in code blocks
 */
function fixCopyButtons() {
    // Adjust CSS for copy buttons
    const style = document.createElement('style');
    style.textContent = `
        div[class*="highlight"] {
            position: relative;
        }
        
        .copybtn {
            position: absolute;
            top: 0;
            right: 0;
            margin: 4px;
            z-index: 10;
            opacity: 0.3;
            transition: opacity 0.2s ease;
            border: none !important;
            background: rgba(255, 255, 255, 0.8) !important;
            border-radius: 4px !important;
            padding: 4px 6px !important;
        }
        
        .copybtn:hover {
            opacity: 1;
        }
        
        .highlight:hover .copybtn {
            opacity: 0.7;
        }
    `;
    document.head.appendChild(style);
    
    // Ensure copy buttons are initialized properly
    document.querySelectorAll('.highlight pre').forEach(function(codeBlock) {
        if (!codeBlock.parentNode.querySelector('.copybtn')) {
            const button = document.createElement('button');
            button.className = 'copybtn';
            button.setAttribute('title', 'Copy to clipboard');
            button.innerHTML = '<i class="fa fa-copy"></i>';
            
            button.addEventListener('click', function() {
                const code = codeBlock.textContent;
                navigator.clipboard.writeText(code).then(function() {
                    button.innerHTML = '<i class="fa fa-check"></i>';
                    setTimeout(function() {
                        button.innerHTML = '<i class="fa fa-copy"></i>';
                    }, 2000);
                }).catch(function(err) {
                    console.error('Could not copy text: ', err);
                    button.innerHTML = '<i class="fa fa-times"></i>';
                    setTimeout(function() {
                        button.innerHTML = '<i class="fa fa-copy"></i>';
                    }, 2000);
                });
            });
            
            codeBlock.parentNode.appendChild(button);
        }
    });
}

/**
 * Add anchor links to headings for easy linking
 */
function addAnchorLinks() {
    // Add CSS for anchor links
    const style = document.createElement('style');
    style.textContent = `
        .section h1[id], .section h2[id], .section h3[id], 
        .section h4[id], .section h5[id], .section h6[id] {
            position: relative;
        }
        
        .headerlink {
            opacity: 0;
            margin-left: 0.5em;
            transition: opacity 0.2s ease;
            color: #3b82f6 !important;
            text-decoration: none !important;
        }
        
        .section h1:hover .headerlink, 
        .section h2:hover .headerlink, 
        .section h3:hover .headerlink,
        .section h4:hover .headerlink,
        .section h5:hover .headerlink,
        .section h6:hover .headerlink {
            opacity: 1;
        }
    `;
    document.head.appendChild(style);
    
    // Add anchor links to all headings with IDs
    document.querySelectorAll('.section h1[id], .section h2[id], .section h3[id], .section h4[id], .section h5[id], .section h6[id]').forEach(function(heading) {
        if (!heading.querySelector('.headerlink')) {
            const anchor = document.createElement('a');
            anchor.className = 'headerlink';
            anchor.href = '#' + heading.id;
            anchor.innerHTML = '¶';
            anchor.setAttribute('title', 'Permalink to this heading');
            heading.appendChild(anchor);
        }
    });
}

/**
 * Enhance code blocks with language labels and improved styling
 */
function enhanceCodeBlocks() {
    // Add CSS for enhanced code blocks
    const style = document.createElement('style');
    style.textContent = `
        div[class*="highlight"] {
            border-radius: 6px;
            margin: 1.5em 0;
            box-shadow: 0 2px 15px rgba(0, 0, 0, 0.05);
            overflow: hidden;
        }
        
        .highlight pre {
            padding: 16px;
            line-height: 1.5;
            font-size: 14px;
            border-radius: 0;
            border: none;
            margin: 0;
        }
        
        .code-label {
            display: block;
            padding: 5px 10px;
            background: rgba(0, 0, 0, 0.05);
            font-size: 12px;
            font-weight: bold;
            color: #666;
            border-bottom: 1px solid rgba(0, 0, 0, 0.1);
        }
        
        html.dark-theme .code-label {
            background: rgba(255, 255, 255, 0.05);
            color: #aaa;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
    `;
    document.head.appendChild(style);
    
    // Add language labels to code blocks
    document.querySelectorAll('div[class*="highlight-"]').forEach(function(codeBlock) {
        // Extract language from class name
        const classes = codeBlock.className.split(' ');
        const highlightClass = classes.find(cls => cls.startsWith('highlight-'));
        
        if (highlightClass && !codeBlock.querySelector('.code-label')) {
            const language = highlightClass.replace('highlight-', '');
            if (language && language !== 'default' && language !== 'none') {
                const label = document.createElement('div');
                label.className = 'code-label';
                label.textContent = language;
                codeBlock.insertBefore(label, codeBlock.firstChild);
            }
        }
    });
}

/**
 * Make tables responsive for better mobile display
 */
function makeTablesResponsive() {
    // Add CSS for responsive tables
    const style = document.createElement('style');
    style.textContent = `
        .table-container {
            width: 100%;
            overflow-x: auto;
            margin-bottom: 20px;
        }
        
        @media (max-width: 768px) {
            .table-container {
                -webkit-overflow-scrolling: touch;
                border-left: 1px solid #e5e5e5;
                border-right: 1px solid #e5e5e5;
                border-radius: 4px;
            }
            
            html.dark-theme .table-container {
                border-color: #444;
            }
        }
    `;
    document.head.appendChild(style);
    
    // Wrap tables in responsive containers
    document.querySelectorAll('table.docutils').forEach(function(table) {
        // Skip if already wrapped
        if (table.parentNode.classList.contains('table-container')) {
            return;
        }
        
        const wrapper = document.createElement('div');
        wrapper.className = 'table-container';
        table.parentNode.insertBefore(wrapper, table);
        wrapper.appendChild(table);
    });
}

/**
 * Fix common mobile layout issues
 */
function fixMobileLayout() {
    // Add CSS fixes for mobile layout
    const style = document.createElement('style');
    style.textContent = `
        @media (max-width: 768px) {
            /* Ensure content doesn't overflow */
            .wy-nav-content {
                padding: 16px;
                overflow-wrap: break-word;
                word-wrap: break-word;
                hyphens: auto;
            }
            
            /* Fix code blocks on mobile */
            .highlight pre {
                white-space: pre-wrap;
            }
            
            /* Improve readability of inline code */
            code {
                word-break: break-word;
            }
            
            /* Ensure images don't overflow */
            img {
                max-width: 100%;
                height: auto;
            }
            
            /* Fix navigation issue on RTD theme */
            .wy-nav-top {
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            
            /* Hide table of contents on very small screens */
            @media (max-width: 400px) {
                .wy-nav-content .contents.local {
                    display: none;
                }
            }
        }
    `;
    document.head.appendChild(style);
    
    // Fix nav menu button on mobile
    const navButton = document.querySelector('.wy-nav-top button');
    if (navButton) {
        navButton.style.display = 'flex';
        navButton.style.alignItems = 'center';
        navButton.style.justifyContent = 'center';
    }
}

/**
 * Enhance search functionality with result highlighting
 */
function enhanceSearch() {
    // Add CSS for search result highlighting
    const style = document.createElement('style');
    style.textContent = `
        .search-highlight {
            background-color: rgba(255, 255, 0, 0.3);
            padding: 0 3px;
            border-radius: 3px;
        }
        
        html.dark-theme .search-highlight {
            background-color: rgba(255, 255, 0, 0.15);
            color: #ffff80;
        }
    `;
    document.head.appendChild(style);
    
    // Check if we're on a search results page
    if (window.location.pathname.includes('search.html')) {
        // Extract search query from URL
        const urlParams = new URLSearchParams(window.location.search);
        const query = urlParams.get('q');
        
        if (query) {
            // Highlight search terms in results
            const searchResults = document.querySelector('.search');
            if (searchResults) {
                // Wait for search results to be populated
                setTimeout(function() {
                    highlightSearchResults(query);
                }, 500);
            }
        }
    }
}

/**
 * Highlight search terms in search results
 */
function highlightSearchResults(query) {
    // Split query into words
    const words = query.split(/\s+/).filter(word => word.length > 2);
    
    // Get all search result items
    const resultItems = document.querySelectorAll('.search li');
    
    resultItems.forEach(function(item) {
        const text = item.innerHTML;
        
        // Highlight each word in the query
        let highlightedText = text;
        words.forEach(function(word) {
            const regex = new RegExp('(' + escapeRegExp(word) + ')', 'gi');
            highlightedText = highlightedText.replace(regex, '<span class="search-highlight">$1</span>');
        });
        
        item.innerHTML = highlightedText;
    });
}

/**
 * Escape string for use in regular expression
 */
function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
