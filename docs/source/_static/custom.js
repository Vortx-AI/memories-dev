// Custom JavaScript for memories-dev documentation

document.addEventListener('DOMContentLoaded', function() {
    // Add copy buttons to code blocks
    addCopyButtons();
    
    // Add collapsible sections
    makeCollapsible();
    
    // Add smooth scrolling for anchor links
    enableSmoothScrolling();
    
    // Add table of contents highlighting
    highlightTableOfContents();
    
    // Add dark mode toggle
    setupDarkModeToggle();
    
    // Add version selector enhancement
    enhanceVersionSelector();
    
    // Add search enhancement
    enhanceSearch();
    
    // Add mermaid diagram zoom
    enableMermaidZoom();
    
    // Add API documentation enhancement
    enhanceAPIDocumentation();
    
    // Enhance code blocks with better styling
    enhanceCodeBlocks();
});

// Add copy buttons to code blocks
function addCopyButtons() {
    // Check if copy buttons are already added by sphinx-copybutton
    if (document.querySelector('.copybtn')) {
        // Enhance existing copy buttons
        document.querySelectorAll('.copybtn').forEach(function(button) {
            button.addEventListener('click', function() {
                button.textContent = 'Copied!';
                setTimeout(function() {
                    button.textContent = '';
                }, 2000);
            });
        });
        return;
    }
    
    // Add copy buttons to code blocks if not already added
    document.querySelectorAll('pre').forEach(function(pre) {
        if (!pre.querySelector('.copybtn')) {
            var button = document.createElement('button');
            button.className = 'copybtn';
            button.textContent = 'Copy';
            
            button.addEventListener('click', function() {
                var code = pre.querySelector('code') ? pre.querySelector('code').textContent : pre.textContent;
                navigator.clipboard.writeText(code).then(function() {
                    button.textContent = 'Copied!';
                    setTimeout(function() {
                        button.textContent = 'Copy';
                    }, 2000);
                }).catch(function(error) {
                    console.error('Could not copy text: ', error);
                    button.textContent = 'Error!';
                    setTimeout(function() {
                        button.textContent = 'Copy';
                    }, 2000);
                });
            });
            
            pre.appendChild(button);
        }
    });
}

// Enhance code blocks with better styling and line numbers
function enhanceCodeBlocks() {
    document.querySelectorAll('div.highlight pre').forEach(function(pre) {
        // Add a subtle glow effect to code blocks
        pre.style.boxShadow = '0 0 10px rgba(80, 250, 123, 0.1)';
        
        // Add line numbers if not already present
        if (!pre.classList.contains('with-line-numbers') && !pre.parentElement.classList.contains('linenos')) {
            pre.classList.add('with-line-numbers');
            
            var code = pre.textContent.split('\n');
            // Remove the last empty line if present
            if (code[code.length - 1] === '') {
                code.pop();
            }
            
            var lineNumbersDiv = document.createElement('div');
            lineNumbersDiv.className = 'line-numbers';
            lineNumbersDiv.style.float = 'left';
            lineNumbersDiv.style.textAlign = 'right';
            lineNumbersDiv.style.color = '#6272a4';
            lineNumbersDiv.style.paddingRight = '10px';
            lineNumbersDiv.style.marginRight = '10px';
            lineNumbersDiv.style.borderRight = '1px solid #334155';
            lineNumbersDiv.style.userSelect = 'none';
            
            var codeContentDiv = document.createElement('div');
            codeContentDiv.className = 'code-content';
            codeContentDiv.style.overflow = 'auto';
            
            for (var i = 0; i < code.length; i++) {
                var lineNumber = document.createElement('div');
                lineNumber.textContent = (i + 1);
                lineNumber.style.paddingRight = '5px';
                lineNumbersDiv.appendChild(lineNumber);
                
                var codeLine = document.createElement('div');
                codeLine.textContent = code[i];
                codeLine.style.fontFamily = 'SFMono-Regular, Consolas, Liberation Mono, Menlo, monospace';
                codeContentDiv.appendChild(codeLine);
            }
            
            // Clear the pre content
            pre.textContent = '';
            
            // Create a wrapper div for flex layout
            var wrapper = document.createElement('div');
            wrapper.style.display = 'flex';
            wrapper.appendChild(lineNumbersDiv);
            wrapper.appendChild(codeContentDiv);
            
            pre.appendChild(wrapper);
        }
        
        // Add language indicator
        var parent = pre.parentElement;
        if (parent && parent.classList.length > 0) {
            // Try to determine the language from class
            var langClass = Array.from(parent.classList).find(cls => cls.startsWith('language-'));
            if (langClass) {
                var lang = langClass.replace('language-', '');
                var langIndicator = document.createElement('div');
                langIndicator.className = 'lang-indicator';
                langIndicator.textContent = lang;
                langIndicator.style.position = 'absolute';
                langIndicator.style.top = '0';
                langIndicator.style.right = '0';
                langIndicator.style.padding = '2px 8px';
                langIndicator.style.fontSize = '0.8em';
                langIndicator.style.backgroundColor = '#0f172a';
                langIndicator.style.color = '#8be9fd';
                langIndicator.style.borderRadius = '0 0 0 4px';
                langIndicator.style.textTransform = 'uppercase';
                langIndicator.style.fontWeight = 'bold';
                
                // Make sure parent has position relative
                if (getComputedStyle(parent).position === 'static') {
                    parent.style.position = 'relative';
                }
                
                parent.appendChild(langIndicator);
            }
        }
    });
}

// Make sections collapsible
function makeCollapsible() {
    document.querySelectorAll('.section').forEach(function(section) {
        var heading = section.querySelector('h2, h3, h4, h5, h6');
        if (heading) {
            heading.style.cursor = 'pointer';
            heading.classList.add('collapsible');
            
            // Add toggle icon
            var icon = document.createElement('span');
            icon.className = 'collapse-icon';
            icon.innerHTML = '▼';
            icon.style.marginLeft = '0.5em';
            icon.style.fontSize = '0.8em';
            heading.appendChild(icon);
            
            heading.addEventListener('click', function(event) {
                if (event.target === heading || event.target === icon) {
                    // Toggle visibility of all siblings until next heading
                    var sibling = heading.nextElementSibling;
                    var isCollapsed = icon.innerHTML === '▶';
                    
                    icon.innerHTML = isCollapsed ? '▼' : '▶';
                    
                    while (sibling && !sibling.matches('h2, h3, h4, h5, h6')) {
                        sibling.style.display = isCollapsed ? '' : 'none';
                        sibling = sibling.nextElementSibling;
                    }
                }
            });
        }
    });
}

// Enable smooth scrolling for anchor links
function enableSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            var targetId = this.getAttribute('href');
            var targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 70, // Adjust for fixed header
                    behavior: 'smooth'
                });
                
                // Update URL without scrolling
                history.pushState(null, null, targetId);
            }
        });
    });
}

// Highlight active section in table of contents
function highlightTableOfContents() {
    var toc = document.querySelector('.wy-menu-vertical');
    if (!toc) return;
    
    var headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
    var tocLinks = toc.querySelectorAll('a');
    
    window.addEventListener('scroll', function() {
        var scrollPosition = window.scrollY;
        
        // Find the current section
        var currentSection = null;
        headings.forEach(function(heading) {
            if (heading.offsetTop - 100 <= scrollPosition) {
                currentSection = heading.id;
            }
        });
        
        // Highlight the corresponding TOC link
        if (currentSection) {
            tocLinks.forEach(function(link) {
                link.classList.remove('active');
                
                var href = link.getAttribute('href');
                if (href && href.includes(currentSection)) {
                    link.classList.add('active');
                }
            });
        }
    });
}

// Setup dark mode toggle
function setupDarkModeToggle() {
    // Create toggle button
    var toggleButton = document.createElement('button');
    toggleButton.id = 'dark-mode-toggle';
    toggleButton.innerHTML = '🌙';
    toggleButton.title = 'Toggle Dark Mode';
    toggleButton.style.position = 'fixed';
    toggleButton.style.bottom = '20px';
    toggleButton.style.right = '20px';
    toggleButton.style.zIndex = '1000';
    toggleButton.style.width = '40px';
    toggleButton.style.height = '40px';
    toggleButton.style.borderRadius = '50%';
    toggleButton.style.backgroundColor = '#0f172a';
    toggleButton.style.color = '#fff';
    toggleButton.style.border = 'none';
    toggleButton.style.cursor = 'pointer';
    toggleButton.style.fontSize = '1.2em';
    toggleButton.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
    
    document.body.appendChild(toggleButton);
    
    // Check for saved preference
    var darkMode = localStorage.getItem('darkMode') === 'true';
    
    // Apply initial mode
    if (darkMode) {
        document.body.classList.add('dark-mode');
        toggleButton.innerHTML = '☀️';
    }
    
    // Toggle dark mode on button click
    toggleButton.addEventListener('click', function() {
        darkMode = !darkMode;
        document.body.classList.toggle('dark-mode');
        toggleButton.innerHTML = darkMode ? '☀️' : '🌙';
        localStorage.setItem('darkMode', darkMode);
    });
    
    // Add dark mode styles
    var style = document.createElement('style');
    style.textContent = `
        .dark-mode {
            --primary-color: #1e293b;
            --primary-light: #334155;
            --primary-dark: #0f172a;
            --accent-color: #3b82f6;
            --accent-light: #60a5fa;
            --accent-dark: #2563eb;
            --text-color: #f8fafc;
            --text-muted: #94a3b8;
            --border-color: #475569;
            --code-bg: #0f172a;
            --code-color: #e2e8f0;
            background-color: #0f172a;
            color: #f8fafc;
        }
        
        .dark-mode a {
            color: #60a5fa;
        }
        
        .dark-mode a:hover {
            color: #93c5fd;
        }
        
        .dark-mode .wy-nav-content {
            background-color: #1e293b;
        }
        
        .dark-mode .wy-side-nav-search {
            background-color: #0f172a;
        }
        
        .dark-mode .wy-nav-side {
            background-color: #0f172a;
        }
        
        .dark-mode .wy-menu-vertical a {
            color: #f8fafc;
        }
        
        .dark-mode .wy-menu-vertical li.current {
            background-color: #334155;
        }
        
        .dark-mode .wy-menu-vertical li.current a {
            color: #f8fafc;
        }
        
        .dark-mode pre {
            background-color: #0f172a;
            border-left-color: #3b82f6;
        }
        
        .dark-mode code {
            background-color: #0f172a;
            color: #e2e8f0;
        }
        
        .dark-mode .admonition {
            background-color: #334155;
        }
        
        .dark-mode .admonition-title {
            background-color: #475569;
        }
        
        .dark-mode table {
            color: #f8fafc;
        }
        
        .dark-mode th {
            background-color: #334155;
        }
        
        .dark-mode tr:nth-child(even) {
            background-color: #1e293b;
        }
        
        .dark-mode tr:nth-child(odd) {
            background-color: #0f172a;
        }
        
        .dark-mode dl.class, .dark-mode dl.function, .dark-mode dl.method, .dark-mode dl.attribute {
            background-color: #1e293b;
            border-color: #475569;
        }
        
        .dark-mode dl.class > dt, .dark-mode dl.function > dt, .dark-mode dl.method > dt, .dark-mode dl.attribute > dt {
            background-color: #0f172a;
            color: #f8fafc;
        }
    `;
    
    document.head.appendChild(style);
}

// Enhance version selector
function enhanceVersionSelector() {
    var versionSelector = document.querySelector('.rst-versions');
    if (!versionSelector) return;
    
    // Add animation to version selector
    versionSelector.addEventListener('click', function() {
        this.classList.toggle('expanded');
    });
    
    // Add styles for animation
    var style = document.createElement('style');
    style.textContent = `
        .rst-versions {
            transition: all 0.3s ease-in-out;
        }
        
        .rst-versions.expanded {
            max-height: 300px;
        }
    `;
    
    document.head.appendChild(style);
}

// Enhance search functionality
function enhanceSearch() {
    var searchInput = document.querySelector('.wy-side-nav-search input[type="text"]');
    if (!searchInput) return;
    
    // Add placeholder text
    searchInput.placeholder = 'Search the documentation...';
    
    // Add clear button
    var clearButton = document.createElement('button');
    clearButton.className = 'search-clear-button';
    clearButton.innerHTML = '×';
    clearButton.style.position = 'absolute';
    clearButton.style.right = '10px';
    clearButton.style.top = '50%';
    clearButton.style.transform = 'translateY(-50%)';
    clearButton.style.background = 'none';
    clearButton.style.border = 'none';
    clearButton.style.fontSize = '1.2em';
    clearButton.style.cursor = 'pointer';
    clearButton.style.color = '#666';
    clearButton.style.display = 'none';
    
    searchInput.parentNode.style.position = 'relative';
    searchInput.parentNode.appendChild(clearButton);
    
    // Show/hide clear button based on input
    searchInput.addEventListener('input', function() {
        clearButton.style.display = this.value ? 'block' : 'none';
    });
    
    // Clear search on button click
    clearButton.addEventListener('click', function() {
        searchInput.value = '';
        searchInput.focus();
        clearButton.style.display = 'none';
    });
}

// Enable zoom for mermaid diagrams
function enableMermaidZoom() {
    document.querySelectorAll('.mermaid').forEach(function(diagram) {
        diagram.style.cursor = 'zoom-in';
        
        diagram.addEventListener('click', function() {
            // Create modal
            var modal = document.createElement('div');
            modal.className = 'mermaid-modal';
            modal.style.position = 'fixed';
            modal.style.top = '0';
            modal.style.left = '0';
            modal.style.width = '100%';
            modal.style.height = '100%';
            modal.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
            modal.style.zIndex = '1001';
            modal.style.display = 'flex';
            modal.style.justifyContent = 'center';
            modal.style.alignItems = 'center';
            modal.style.cursor = 'zoom-out';
            
            // Clone diagram
            var clonedDiagram = diagram.cloneNode(true);
            clonedDiagram.style.transform = 'scale(1.5)';
            clonedDiagram.style.maxWidth = '90%';
            clonedDiagram.style.maxHeight = '90%';
            
            modal.appendChild(clonedDiagram);
            document.body.appendChild(modal);
            
            // Close modal on click
            modal.addEventListener('click', function() {
                document.body.removeChild(modal);
            });
        });
    });
}

// Enhance API documentation
function enhanceAPIDocumentation() {
    document.querySelectorAll('dl.class, dl.function, dl.method, dl.attribute').forEach(function(element) {
        // Add hover effect
        element.addEventListener('mouseenter', function() {
            this.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)';
            this.style.transform = 'translateY(-2px)';
            this.style.transition = 'all 0.2s ease-in-out';
        });
        
        element.addEventListener('mouseleave', function() {
            this.style.boxShadow = 'none';
            this.style.transform = 'translateY(0)';
        });
        
        // Add collapsible parameters
        var dt = element.querySelector('dt');
        if (dt) {
            var paramSection = element.querySelector('.field-list');
            if (paramSection) {
                var toggleButton = document.createElement('button');
                toggleButton.className = 'param-toggle';
                toggleButton.innerHTML = 'Toggle Parameters';
                toggleButton.style.fontSize = '0.8em';
                toggleButton.style.padding = '0.2em 0.5em';
                toggleButton.style.marginTop = '0.5em';
                toggleButton.style.backgroundColor = '#f1f5f9';
                toggleButton.style.border = '1px solid #e2e8f0';
                toggleButton.style.borderRadius = '4px';
                toggleButton.style.cursor = 'pointer';
                
                dt.appendChild(toggleButton);
                
                toggleButton.addEventListener('click', function(e) {
                    e.stopPropagation();
                    paramSection.style.display = paramSection.style.display === 'none' ? 'block' : 'none';
                });
            }
        }
    });
} 