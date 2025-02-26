# Professional Developer Theme for Memories-Dev Documentation

## Overview

This README provides technical details about the Professional Developer Theme implementation for the Memories-Dev documentation. The theme is designed to enhance readability and provide a clean, professional experience for developers working with the Memories-Dev framework.

## Files

The theme consists of three main files:

1. `custom.css` - Main styling for the documentation
2. `code-highlight.css` - Syntax highlighting for code blocks
3. `custom.js` - JavaScript enhancements for navigation and interactivity

## CSS Implementation

### Color Variables

The theme uses CSS variables for consistent colors throughout:

```css
:root {
    --primary-color: #1a1a1a;
    --primary-light: #f8f9fa;
    --primary-dark: #2c3e50;
    --accent-color: #4285f4;
    --accent-light: #8ab4f8;
    --accent-dark: #1a73e8;
    --text-color: #1a1a1a;
    --text-muted: #6c757d;
    --border-color: #dee2e6;
    --code-bg: #202124;
    --code-color: #e8eaed;
}
```

### Typography

System font stack for optimal readability across platforms:

```css
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, Cantarell, "Helvetica Neue", sans-serif;
    line-height: 1.5;
    color: var(--text-color);
}

code, pre {
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
}
```

### Code Block Styling

Clean, professional code blocks with syntax highlighting:

```css
div.highlight {
    background-color: var(--code-bg);
    border-radius: 4px;
    margin: 1.5em 0;
    position: relative;
    overflow: hidden;
}

div.highlight pre {
    background-color: var(--code-bg);
    color: var(--code-color);
    border-radius: 4px;
    padding: 1.2em;
    margin: 0;
    overflow: auto;
    border-left: 4px solid var(--accent-color);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}
```

## JavaScript Features

### Copy Button for Code Blocks

```javascript
function addCopyButtons() {
    const codeBlocks = document.querySelectorAll('div.highlight');
    
    codeBlocks.forEach(function(codeBlock) {
        const button = document.createElement('button');
        button.className = 'copybtn';
        button.title = 'Copy to clipboard';
        
        button.addEventListener('click', function() {
            const code = codeBlock.querySelector('pre').textContent;
            
            navigator.clipboard.writeText(code).then(function() {
                // Visual feedback
                button.classList.add('copied');
                // Reset after 2 seconds
                setTimeout(function() {
                    button.classList.remove('copied');
                }, 2000);
            });
        });
        
        codeBlock.appendChild(button);
    });
}
```

### Navigation Enhancements

```javascript
function enhanceNavigation() {
    // Highlight current page in navigation
    highlightCurrentPage();
    
    // Add smooth scrolling to anchor links
    addSmoothScrolling();
    
    // Expand navigation sections for current page
    expandCurrentSection();
}
```

### Responsive Design

```javascript
function addResponsiveBehavior() {
    // Add toggle button for mobile navigation
    addMobileNavToggle();
    
    // Handle window resize events
    handleResize();
}
```

## Integration with Sphinx

The theme is integrated with Sphinx through the `conf.py` file:

```python
html_static_path = ['_static']
html_css_files = [
    'custom.css',
    'code-highlight.css',
]
html_js_files = [
    'custom.js',
]
```

## Browser Compatibility

The theme has been tested on:
- Chrome (latest versions)
- Firefox (latest versions)
- Safari (latest versions)
- Edge (latest versions)

## Accessibility Considerations

The theme adheres to WCAG standards:
- Color contrast ratios meet AA standards
- Semantic HTML structure
- Keyboard navigation support
- Screen reader compatibility
- Responsive design for various devices

## Customization

Users can customize the theme through:
- Browser font size controls
- Print-specific styling
- CSS variables for color adjustments

## Future Improvements

Potential enhancements for future versions:
- Dark mode toggle
- User preference saving
- Additional syntax highlighting themes
- Performance optimizations
- Enhanced mobile experience

## Credits

The Professional Developer Theme was developed for the Memories-Dev project, with inspiration from modern documentation sites like Google Developer Documentation, MDN Web Docs, and ReadTheDocs. 