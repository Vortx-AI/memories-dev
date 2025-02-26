// Code highlighting enhancement script for memories-dev documentation
document.addEventListener('DOMContentLoaded', function() {
    // Add copy buttons to all code blocks
    const codeBlocks = document.querySelectorAll('.highlight');
    
    codeBlocks.forEach(function(block, index) {
        // Skip if already has copy button
        if (block.querySelector('.copy-btn')) {
            return;
        }
        
        // Create copy button
        const button = document.createElement('button');
        button.className = 'copy-btn';
        button.textContent = 'Copy';
        button.title = 'Copy code to clipboard';
        
        // Add language tag
        let language = '';
        const classes = block.className.split(' ');
        for (const cls of classes) {
            if (cls.startsWith('highlight-')) {
                language = cls.replace('highlight-', '');
                break;
            }
        }
        
        if (language && language !== 'default' && language !== 'python') {
            const languageTag = document.createElement('span');
            languageTag.className = 'highlight-language';
            languageTag.textContent = language;
            block.appendChild(languageTag);
        }
        
        // Add copy functionality
        button.addEventListener('click', function() {
            const pre = block.querySelector('pre');
            const code = pre.textContent;
            
            navigator.clipboard.writeText(code).then(function() {
                button.textContent = 'Copied!';
                setTimeout(function() {
                    button.textContent = 'Copy';
                }, 2000);
            }).catch(function(err) {
                button.textContent = 'Failed';
                console.error('Failed to copy code: ', err);
                setTimeout(function() {
                    button.textContent = 'Copy';
                }, 2000);
            });
        });
        
        // Add button to block
        block.appendChild(button);
    });
    
    // Add filename display
    const codeElements = document.querySelectorAll('div[class*="highlight-"]');
    codeElements.forEach(function(element) {
        // Get filename attribute if exists
        const caption = element.querySelector('div.code-block-caption');
        if (caption) {
            const filename = caption.textContent.trim();
            
            // Create filename element
            const filenameElement = document.createElement('div');
            filenameElement.className = 'highlight-filename';
            filenameElement.textContent = filename;
            
            // Insert before code block
            const highlight = element.querySelector('.highlight');
            if (highlight) {
                element.insertBefore(filenameElement, highlight);
            }
            
            // Hide the original caption
            caption.style.display = 'none';
        }
    });

    // Add line numbers to code blocks if not already present
    const preElements = document.querySelectorAll('.highlight pre:not(.linenos)');
    preElements.forEach(function(pre) {
        // Skip if already has line numbers
        if (pre.classList.contains('with-line-numbers') || pre.parentElement.querySelector('.linenos')) {
            return;
        }

        const code = pre.textContent;
        const lines = code.split('\n');
        
        // Only add line numbers if there's more than 1 line
        if (lines.length > 1) {
            pre.classList.add('with-line-numbers');
            
            // Create line number container
            const lineNumbersContainer = document.createElement('div');
            lineNumbersContainer.className = 'linenos';
            
            // Add line numbers
            for (let i = 1; i <= lines.length; i++) {
                const lineNumber = document.createElement('span');
                lineNumber.className = 'lineno';
                lineNumber.textContent = i;
                lineNumber.setAttribute('data-line-number', i);
                lineNumbersContainer.appendChild(lineNumber);
                
                // Add line break except for last line
                if (i < lines.length) {
                    lineNumbersContainer.appendChild(document.createElement('br'));
                }
            }
            
            // Insert line numbers before code
            pre.parentElement.insertBefore(lineNumbersContainer, pre);
        }
    });

    // Handle collapsible code blocks
    const longCodeBlocks = document.querySelectorAll('.highlight pre');
    longCodeBlocks.forEach(function(pre) {
        const lines = pre.textContent.split('\n').length;
        
        // Only make collapsible if it's a long code block (more than 15 lines)
        if (lines > 15) {
            const container = pre.closest('.highlight');
            
            // Create collapse/expand button
            const toggleButton = document.createElement('button');
            toggleButton.className = 'code-collapse-btn';
            toggleButton.textContent = 'Collapse';
            toggleButton.title = 'Toggle code block visibility';
            
            // Add toggle functionality
            let isCollapsed = false;
            toggleButton.addEventListener('click', function() {
                if (isCollapsed) {
                    pre.style.maxHeight = 'none';
                    toggleButton.textContent = 'Collapse';
                } else {
                    pre.style.maxHeight = '200px';
                    toggleButton.textContent = 'Expand';
                }
                isCollapsed = !isCollapsed;
            });
            
            // Add button to container
            container.appendChild(toggleButton);
        }
    });
}); 