/**
 * Documentation Fixes for Memories-Dev
 * 
 * This script addresses various rendering issues in the documentation:
 * - Fixes "On This Page" section UI glitches
 * - Corrects title underline rendering
 * - Improves math equation display
 * - Enhances mobile responsiveness
 * - Fixes z-index and positioning issues
 */

document.addEventListener('DOMContentLoaded', function() {
    // Apply all fixes
    fixOnThisPageSection();
    fixTitleUnderlines();
    enhanceMathRendering();
    fixMermaidDiagrams();
    fixMissingReferences();
    improveResponsiveness();
    fixZIndexIssues();
    
    // Apply book-like styling to elements
    applyBookStyling();
    
    // Enhance code blocks
    enhanceCodeBlocks();
    
    // Fix mobile display issues
    fixMobileIssues();
    
    // Add smooth scrolling for in-page links
    addSmoothScrolling();
    
    // Fix image display issues
    fixImageDisplay();
    
    // Add table of contents improvements
    enhanceTableOfContents();
});

/**
 * Fix the "On This Page" section that causes UI glitches
 */
function fixOnThisPageSection() {
    // Get the "On This Page" section
    const onThisPageSection = document.querySelector('.wy-nav-content .contents.local');
    
    // Check if the section exists
    if (!onThisPageSection) {
        return;
    }
    
    // Check if we should completely disable the section based on configuration
    const disableOnThisPage = window.DOCUMENTATION_OPTIONS && 
                             window.DOCUMENTATION_OPTIONS.DISABLE_ON_THIS_PAGE === true;
    
    if (disableOnThisPage) {
        // Completely remove the section if disabled in configuration
        onThisPageSection.style.display = 'none';
        return;
    }
    
    // Fix positioning and z-index issues
    onThisPageSection.style.position = 'relative';
    onThisPageSection.style.zIndex = '10';
    
    // Add proper spacing and fix margins
    onThisPageSection.style.marginBottom = '2rem';
    onThisPageSection.style.padding = '1rem';
    
    // Fix background and borders
    onThisPageSection.style.backgroundColor = '#f8f9fa';
    onThisPageSection.style.border = '1px solid #e5e5e5';
    onThisPageSection.style.borderRadius = '4px';
    onThisPageSection.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.05)';
    
    // Update the title
    const title = onThisPageSection.querySelector('.topic-title');
    if (title) {
        title.textContent = 'On This Page';
        title.style.fontWeight = '600';
        title.style.marginBottom = '10px';
        title.style.color = '#333';
    }
    
    // Fix nested lists to prevent overflow
    const lists = onThisPageSection.querySelectorAll('ul');
    lists.forEach(list => {
        list.style.marginBottom = '0';
        list.style.paddingLeft = '1.5rem';
        
        // Fix list items
        const items = list.querySelectorAll('li');
        items.forEach(item => {
            item.style.marginBottom = '5px';
            
            // Fix links
            const links = item.querySelectorAll('a');
            links.forEach(link => {
                link.style.color = '#3b82f6';
                link.style.textDecoration = 'none';
                
                // Add hover effect
                link.addEventListener('mouseenter', function() {
                    this.style.textDecoration = 'underline';
                });
                
                link.addEventListener('mouseleave', function() {
                    this.style.textDecoration = 'none';
                });
            });
        });
    });
    
    // Handle mobile devices
    function handleResize() {
        if (window.innerWidth <= 768) {
            onThisPageSection.style.display = 'none';
        } else {
            onThisPageSection.style.display = disableOnThisPage ? 'none' : 'block';
        }
    }
    
    // Initial check
    handleResize();
    
    // Add resize listener
    window.addEventListener('resize', handleResize);
    
    // Fix any parent container issues
    const parentContainer = onThisPageSection.parentElement;
    if (parentContainer) {
        parentContainer.style.overflow = 'visible';
    }
}

/**
 * Fix title underlines that are too short
 */
function fixTitleUnderlines() {
    // Find all section titles
    const sectionTitles = document.querySelectorAll('.section > h1, .section > h2, .section > h3, .section > h4, .section > h5, .section > h6');
    
    sectionTitles.forEach(title => {
        // Check if this title has an underline that might be too short
        const nextElement = title.nextElementSibling;
        if (nextElement && nextElement.tagName === 'HR') {
            // Ensure the underline is at least as wide as the title
            nextElement.style.width = '100%';
            nextElement.style.marginTop = '0.2em';
            nextElement.style.marginBottom = '0.7em';
            nextElement.style.border = 'none';
            nextElement.style.borderBottom = '1px solid #e5e5e5';
        }
    });
}

/**
 * Enhance math equation rendering
 */
function enhanceMathRendering() {
    // Wait for MathJax to be loaded
    if (typeof window.MathJax !== 'undefined') {
        // Configure MathJax if needed
        if (window.MathJax.Hub) {
            window.MathJax.Hub.Config({
                tex2jax: {
                    inlineMath: [['$', '$'], ['\\(', '\\)']],
                    displayMath: [['$$', '$$'], ['\\[', '\\]']],
                    processEscapes: true
                },
                "HTML-CSS": { 
                    linebreaks: { automatic: true },
                    scale: 100,
                    styles: {
                        ".MathJax_Display": { margin: "0.5em 0" }
                    }
                }
            });
            
            // Reprocess the page
            window.MathJax.Hub.Queue(["Typeset", window.MathJax.Hub]);
        } else if (window.MathJax.typeset) {
            // MathJax v3
            window.MathJax.typeset();
        }
    }
    
    // Add custom styling for math elements
    const mathElements = document.querySelectorAll('.math');
    mathElements.forEach(element => {
        element.style.maxWidth = '100%';
        element.style.overflowX = 'auto';
        element.style.padding = '0.5em 0';
    });
}

/**
 * Fix Mermaid diagrams rendering
 */
function fixMermaidDiagrams() {
    // Check if mermaid is available
    if (typeof window.mermaid !== 'undefined') {
        // Initialize mermaid with custom settings
        window.mermaid.initialize({
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose',
            flowchart: {
                useMaxWidth: true,
                htmlLabels: true
            },
            fontSize: 16
        });
        
        // Find all mermaid diagram containers
        const mermaidDivs = document.querySelectorAll('.mermaid');
        mermaidDivs.forEach(div => {
            // Add responsive styling
            div.style.maxWidth = '100%';
            div.style.overflowX = 'auto';
            div.style.margin = '1em 0';
            
            // Force re-render
            if (window.mermaid.contentLoaded) {
                window.mermaid.contentLoaded();
            } else if (window.mermaid.init) {
                window.mermaid.init(undefined, div);
            }
        });
    } else {
        // If mermaid is not available, try to load it
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/mermaid@8.13.3/dist/mermaid.min.js';
        script.onload = function() {
            if (window.mermaid) {
                window.mermaid.initialize({
                    startOnLoad: true
                });
            }
        };
        document.head.appendChild(script);
    }
}

/**
 * Fix missing references and broken links
 */
function fixMissingReferences() {
    // Find all broken reference links
    const brokenLinks = document.querySelectorAll('a.reference.internal.pending');
    
    brokenLinks.forEach(link => {
        // Get the text of the link
        const linkText = link.textContent.trim();
        
        // Make the link non-clickable but still visible
        link.style.color = '#6c757d';
        link.style.textDecoration = 'none';
        link.style.cursor = 'default';
        link.style.borderBottom = '1px dotted #6c757d';
        
        // Add a title attribute to explain
        link.title = `Reference to "${linkText}" is not available yet`;
        
        // Prevent the default click behavior
        link.addEventListener('click', function(e) {
            e.preventDefault();
        });
    });
}

/**
 * Improve responsiveness for mobile devices
 */
function improveResponsiveness() {
    // Check if we're on a mobile device
    const isMobile = window.innerWidth <= 768;
    
    if (isMobile) {
        // Fix table display on mobile
        const tables = document.querySelectorAll('table.docutils');
        tables.forEach(table => {
            table.style.display = 'block';
            table.style.width = '100%';
            table.style.overflowX = 'auto';
        });
        
        // Fix code blocks on mobile
        const codeBlocks = document.querySelectorAll('pre');
        codeBlocks.forEach(block => {
            block.style.whiteSpace = 'pre';
            block.style.overflowX = 'auto';
            block.style.fontSize = '13px';
        });
        
        // Improve form elements on mobile
        const formInputs = document.querySelectorAll('input[type="text"], input[type="email"], input[type="search"], textarea');
        formInputs.forEach(input => {
            input.style.fontSize = '16px';
        });
    }
    
    // Add resize listener for responsive adjustments
    window.addEventListener('resize', function() {
        const newIsMobile = window.innerWidth <= 768;
        if (newIsMobile !== isMobile) {
            // Reload the page if switching between mobile and desktop
            // This ensures all responsive elements are properly adjusted
            window.location.reload();
        }
    });
}

/**
 * Fix z-index and positioning issues
 */
function fixZIndexIssues() {
    // Fix sidebar z-index
    const sidebar = document.querySelector('.wy-nav-side');
    if (sidebar) {
        sidebar.style.zIndex = '200';
    }
    
    // Fix mobile navigation z-index
    const mobileNav = document.querySelector('.wy-nav-top');
    if (mobileNav) {
        mobileNav.style.zIndex = '300';
    }
    
    // Fix dropdown menus z-index
    const dropdowns = document.querySelectorAll('.wy-dropdown, .wy-dropdown-menu');
    dropdowns.forEach(dropdown => {
        dropdown.style.zIndex = '250';
    });
    
    // Fix tooltips z-index
    const tooltips = document.querySelectorAll('.tooltip');
    tooltips.forEach(tooltip => {
        tooltip.style.zIndex = '400';
    });
    
    // Fix copy buttons z-index
    const copyButtons = document.querySelectorAll('.copybtn');
    copyButtons.forEach(button => {
        button.style.zIndex = '100';
    });
} 