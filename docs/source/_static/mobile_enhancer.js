// Mobile Enhancer for memories-dev documentation
document.addEventListener('DOMContentLoaded', function() {
    // Initialize mobile enhancer
    initializeMobileEnhancer();
});

/**
 * Initialize all mobile enhancements
 */
function initializeMobileEnhancer() {
    // Check if mobile enhancer is enabled
    const enableMobileEnhancer = document.querySelector('meta[name="enable-mobile-enhancer"]');
    if (enableMobileEnhancer && enableMobileEnhancer.getAttribute('content') === 'false') {
        return;
    }

    // Add mobile navigation
    addMobileNavigation();
    
    // Fix "On This Page" section
    fixOnThisPageSection();
    
    // Handle scroll events
    handleScrollEvents();
    
    // Fix inconsistent themes
    fixInconsistentThemes();
    
    // Improve table responsiveness
    improveTableResponsiveness();
    
    // Enhance code blocks for mobile
    enhanceCodeBlocksForMobile();
    
    // Fix formula rendering on mobile
    fixFormulaRenderingOnMobile();
    
    // Add orientation change handlers
    addOrientationChangeHandlers();
    
    // Fix sidebar issues
    fixSidebarIssues();
    
    // Fix RTD theme issues
    fixRtdThemeIssues();
}

/**
 * Add mobile navigation enhancements
 */
function addMobileNavigation() {
    // Create mobile navigation overlay
    const overlay = document.createElement('div');
    overlay.className = 'mobile-nav-overlay';
    document.body.appendChild(overlay);
    
    // Add click event to overlay to close navigation
    overlay.addEventListener('click', function() {
        document.body.classList.remove('nav-open');
        const sidebar = document.querySelector('.wy-nav-side');
        const content = document.querySelector('.wy-nav-content-wrap');
        
        if (sidebar) sidebar.classList.remove('shift');
        if (content) content.classList.remove('shift');
    });
    
    // Add click event to mobile menu button
    const menuButton = document.querySelector('.wy-nav-top i');
    if (menuButton) {
        menuButton.addEventListener('click', function(e) {
            e.preventDefault();
            document.body.classList.toggle('nav-open');
            
            const sidebar = document.querySelector('.wy-nav-side');
            const content = document.querySelector('.wy-nav-content-wrap');
            
            if (sidebar) sidebar.classList.toggle('shift');
            if (content) content.classList.toggle('shift');
        });
    }
    
    // Fix RTD theme mobile navigation
    const rtdNav = document.querySelector('.wy-nav-side');
    if (rtdNav) {
        // Ensure proper scroll container
        if (!document.querySelector('.wy-side-scroll')) {
            const scrollContainer = document.createElement('div');
            scrollContainer.className = 'wy-side-scroll';
            
            // Move all children to the scroll container
            while (rtdNav.firstChild) {
                scrollContainer.appendChild(rtdNav.firstChild);
            }
            
            rtdNav.appendChild(scrollContainer);
        }
        
        // Ensure proper width
        rtdNav.style.width = '300px';
        
        // Fix z-index
        rtdNav.style.zIndex = '200';
    }
}

/**
 * Fix "On This Page" section
 */
function fixOnThisPageSection() {
    // Get all "On This Page" sections
    const onThisPageSections = document.querySelectorAll('.contents.local, .contents.topic');
    
    onThisPageSections.forEach(section => {
        // Remove any fixed positioning
        section.style.position = 'relative';
        section.style.top = 'auto';
        section.style.right = 'auto';
        section.style.maxHeight = 'none';
        section.style.overflow = 'visible';
        
        // Add proper styling
        section.style.backgroundColor = 'var(--bg-secondary, #242424)';
        section.style.border = '1px solid var(--border, #3a3a3a)';
        section.style.borderRadius = '4px';
        section.style.padding = '1.5em';
        section.style.margin = '1.5em 0';
        section.style.width = 'auto';
        section.style.maxWidth = '100%';
        section.style.boxShadow = '0 2px 5px var(--shadow, rgba(0, 0, 0, 0.2))';
        
        // Add class for styling
        section.classList.add('on-this-page-fixed');
    });
    
    // Add CSS for "On This Page" section
    const style = document.createElement('style');
    style.textContent = `
        .on-this-page-fixed {
            position: relative !important;
            top: auto !important;
            right: auto !important;
            max-height: none !important;
            overflow: visible !important;
            background-color: var(--bg-secondary, #242424) !important;
            border: 1px solid var(--border, #3a3a3a) !important;
            border-radius: 4px !important;
            padding: 1.5em !important;
            margin: 1.5em 0 !important;
            width: auto !important;
            max-width: 100% !important;
            box-shadow: 0 2px 5px var(--shadow, rgba(0, 0, 0, 0.2)) !important;
        }
        
        .on-this-page-fixed .topic-title {
            font-weight: 600 !important;
            color: var(--text-color, #e8e8e8) !important;
            margin-top: 0 !important;
            margin-bottom: 1em !important;
            font-size: 1.1em !important;
            border-bottom: 1px solid var(--border-light, #444444) !important;
            padding-bottom: 0.5em !important;
        }
        
        .on-this-page-fixed ul {
            list-style-type: none !important;
            padding-left: 0.5em !important;
            margin: 0 !important;
        }
        
        .on-this-page-fixed li {
            margin-bottom: 0.5em !important;
            position: relative !important;
            padding-left: 1em !important;
        }
        
        .on-this-page-fixed li::before {
            content: "•" !important;
            position: absolute !important;
            left: 0 !important;
            color: var(--accent, #4d8bff) !important;
        }
        
        .on-this-page-fixed a {
            color: var(--text-secondary, #b0b0b0) !important;
            text-decoration: none !important;
            transition: color 0.2s ease !important;
        }
        
        .on-this-page-fixed a:hover {
            color: var(--accent, #4d8bff) !important;
            text-decoration: none !important;
        }
    `;
    document.head.appendChild(style);
}

/**
 * Handle scroll events
 */
function handleScrollEvents() {
    // Get all fixed elements
    const fixedElements = document.querySelectorAll('.wy-nav-side, .wy-side-nav-search, .rst-versions');
    
    // Add scroll event listener
    window.addEventListener('scroll', function() {
        // Ensure fixed elements don't overlap
        fixedElements.forEach(element => {
            if (element.classList.contains('wy-nav-side')) {
                element.style.zIndex = '200';
            } else if (element.classList.contains('wy-side-nav-search')) {
                element.style.zIndex = '201';
            } else if (element.classList.contains('rst-versions')) {
                element.style.zIndex = '199';
            }
        });
    });
}

/**
 * Fix inconsistent themes
 */
function fixInconsistentThemes() {
    // Add CSS to fix inconsistent themes
    const style = document.createElement('style');
    style.textContent = `
        /* Ensure consistent background color */
        body {
            background-color: var(--bg-color, #1a1a1a) !important;
            color: var(--text-color, #e8e8e8) !important;
        }
        
        /* Fix table colors */
        .rst-content table.docutils {
            border: 1px solid var(--border, #3a3a3a) !important;
            background-color: var(--bg-secondary, #242424) !important;
        }
        
        .rst-content table.docutils thead {
            background-color: var(--bg-tertiary, #2d2d2d) !important;
        }
        
        .rst-content table.docutils td, 
        .rst-content table.docutils th {
            border: 1px solid var(--border, #3a3a3a) !important;
            color: var(--text-color, #e8e8e8) !important;
        }
        
        /* Fix RTD versions panel */
        .rst-versions {
            background-color: var(--bg-tertiary, #2d2d2d) !important;
            border-top: 1px solid var(--border, #3a3a3a) !important;
        }
        
        .rst-versions .rst-current-version {
            background-color: var(--bg-secondary, #242424) !important;
            color: var(--text-secondary, #b0b0b0) !important;
        }
        
        .rst-versions .rst-other-versions {
            background-color: var(--bg-tertiary, #2d2d2d) !important;
        }
        
        .rst-versions .rst-other-versions a {
            color: var(--text-secondary, #b0b0b0) !important;
        }
        
        .rst-versions .rst-other-versions hr {
            border-color: var(--border, #3a3a3a) !important;
        }
        
        /* Fix RTD ethical ads */
        .ethical-rtd, 
        .ethical-dark-theme .ethical-sidebar {
            background-color: var(--bg-secondary, #242424) !important;
            border: 1px solid var(--border, #3a3a3a) !important;
            color: var(--text-secondary, #b0b0b0) !important;
        }
        
        .ethical-rtd a {
            color: var(--accent, #4d8bff) !important;
        }
        
        /* Fix highlighted text */
        .highlighted {
            background-color: var(--accent-light, rgba(77, 139, 255, 0.1)) !important;
            color: var(--text-color, #e8e8e8) !important;
        }
        
        /* Fix math formulas */
        .math {
            background-color: var(--bg-secondary, #242424) !important;
            color: var(--text-color, #e8e8e8) !important;
        }
        
        /* Fix code blocks */
        .rst-content div[class^="highlight"] {
            background-color: var(--code-bg, #2a2a2a) !important;
        }
        
        .rst-content div[class^="highlight"] pre {
            color: var(--code-text, #e0e0e0) !important;
        }
        
        /* Fix admonitions */
        .admonition {
            background-color: var(--bg-secondary, #242424) !important;
        }
        
        /* Fix search results */
        #search-results .search li {
            border-bottom: 1px solid var(--border-light, #444444) !important;
        }
        
        #search-results .context {
            color: var(--text-secondary, #b0b0b0) !important;
        }
        
        #search-results .highlighted {
            background-color: var(--accent-light, rgba(77, 139, 255, 0.1)) !important;
            color: var(--text-color, #e8e8e8) !important;
        }
    `;
    document.head.appendChild(style);
}

/**
 * Improve table responsiveness
 */
function improveTableResponsiveness() {
    // Get all tables
    const tables = document.querySelectorAll('.rst-content table.docutils');
    
    tables.forEach(table => {
        // Create responsive wrapper
        const wrapper = document.createElement('div');
        wrapper.className = 'table-responsive';
        
        // Insert wrapper before table
        table.parentNode.insertBefore(wrapper, table);
        
        // Move table into wrapper
        wrapper.appendChild(table);
    });
    
    // Add CSS for responsive tables
    const style = document.createElement('style');
    style.textContent = `
        .table-responsive {
            display: block;
            width: 100%;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            margin-bottom: 1.5em;
        }
    `;
    document.head.appendChild(style);
}

/**
 * Enhance code blocks for mobile
 */
function enhanceCodeBlocksForMobile() {
    // Get all code blocks
    const codeBlocks = document.querySelectorAll('.rst-content div[class^="highlight"]');
    
    codeBlocks.forEach(block => {
        // Add mobile-friendly class
        block.classList.add('mobile-friendly-code');
        
        // Ensure copy button is visible
        const copyBtn = block.querySelector('.copybtn');
        if (copyBtn) {
            copyBtn.style.opacity = '0.7';
        }
    });
}

/**
 * Fix formula rendering on mobile
 */
function fixFormulaRenderingOnMobile() {
    // Get all math formulas
    const formulas = document.querySelectorAll('.math');
    
    formulas.forEach(formula => {
        // Add mobile-friendly class
        formula.classList.add('mobile-friendly-formula');
        
        // Create responsive wrapper
        const wrapper = document.createElement('div');
        wrapper.className = 'formula-responsive';
        
        // Insert wrapper before formula
        formula.parentNode.insertBefore(wrapper, formula);
        
        // Move formula into wrapper
        wrapper.appendChild(formula);
    });
    
    // Add CSS for responsive formulas
    const style = document.createElement('style');
    style.textContent = `
        .formula-responsive {
            display: block;
            width: 100%;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            margin: 1em 0;
        }
        
        .mobile-friendly-formula {
            background-color: var(--bg-secondary, #242424);
            padding: 0.5em;
            border-radius: 4px;
            display: inline-block;
            min-width: 100%;
        }
    `;
    document.head.appendChild(style);
}

/**
 * Add orientation change handlers
 */
function addOrientationChangeHandlers() {
    // Add resize event listener
    window.addEventListener('resize', function() {
        // Fix "On This Page" section
        fixOnThisPageSection();
        
        // Fix sidebar issues
        fixSidebarIssues();
    });
    
    // Add orientation change event listener
    window.addEventListener('orientationchange', function() {
        // Fix "On This Page" section
        fixOnThisPageSection();
        
        // Fix sidebar issues
        fixSidebarIssues();
    });
}

/**
 * Fix sidebar issues
 */
function fixSidebarIssues() {
    // Get sidebar
    const sidebar = document.querySelector('.wy-nav-side');
    
    if (sidebar) {
        // Ensure proper width
        sidebar.style.width = '300px';
        
        // Ensure proper z-index
        sidebar.style.zIndex = '200';
        
        // Ensure proper overflow
        sidebar.style.overflow = 'hidden';
        
        // Get scroll container
        const scrollContainer = sidebar.querySelector('.wy-side-scroll');
        
        if (scrollContainer) {
            // Ensure proper width
            scrollContainer.style.width = '320px';
            
            // Ensure proper height
            scrollContainer.style.height = '100%';
            
            // Ensure proper overflow
            scrollContainer.style.overflowY = 'auto';
            scrollContainer.style.overflowX = 'hidden';
        }
    }
    
    // Fix navigation menu
    const navMenu = document.querySelector('.wy-menu-vertical');
    
    if (navMenu) {
        // Ensure proper width
        navMenu.style.width = '300px';
    }
    
    // Fix search box
    const searchBox = document.querySelector('.wy-side-nav-search');
    
    if (searchBox) {
        // Ensure proper z-index
        searchBox.style.zIndex = '201';
    }
    
    // Fix versions panel
    const versionsPanel = document.querySelector('.rst-versions');
    
    if (versionsPanel) {
        // Ensure proper z-index
        versionsPanel.style.zIndex = '199';
    }
}

/**
 * Fix RTD theme issues
 */
function fixRtdThemeIssues() {
    // Add CSS to fix RTD theme issues
    const style = document.createElement('style');
    style.textContent = `
        /* Fix RTD theme sidebar */
        .wy-nav-side {
            background-color: var(--bg-secondary, #242424) !important;
            border-right: 1px solid var(--border, #3a3a3a) !important;
            width: 300px !important;
            position: fixed !important;
            top: 0 !important;
            bottom: 0 !important;
            left: 0 !important;
            overflow: hidden !important;
            z-index: 200 !important;
            transition: transform 0.3s ease !important;
        }
        
        /* Fix RTD theme scroll container */
        .wy-side-scroll {
            width: 320px !important;
            height: 100% !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            position: relative !important;
            padding-bottom: 60px !important;
        }
        
        /* Fix RTD theme navigation menu */
        .wy-menu-vertical {
            width: 300px !important;
            padding: 0 !important;
        }
        
        /* Fix RTD theme search box */
        .wy-side-nav-search {
            background-color: var(--bg-tertiary, #2d2d2d) !important;
            padding: 1em !important;
            margin-bottom: 0 !important;
            z-index: 201 !important;
        }
        
        /* Fix RTD theme content area */
        .wy-nav-content-wrap {
            background-color: var(--bg-color, #1a1a1a) !important;
            margin-left: 300px !important;
            position: relative !important;
            min-height: 100vh !important;
            transition: margin-left 0.3s ease !important;
        }
        
        /* Fix RTD theme content */
        .wy-nav-content {
            background-color: var(--bg-color, #1a1a1a) !important;
            max-width: 900px !important;
            margin: 0 auto !important;
            padding: 2em 3em !important;
        }
        
        /* Fix RTD theme mobile navigation */
        @media screen and (max-width: 768px) {
            .wy-nav-side {
                transform: translateX(-100%) !important;
            }
            
            .wy-nav-side.shift {
                transform: translateX(0) !important;
            }
            
            .wy-nav-content-wrap {
                margin-left: 0 !important;
            }
            
            .wy-nav-content-wrap.shift {
                position: fixed !important;
                min-width: 100% !important;
                left: 300px !important;
                top: 0 !important;
                height: 100% !important;
                overflow: hidden !important;
            }
            
            body.nav-open .mobile-nav-overlay {
                display: block !important;
            }
        }
    `;
    document.head.appendChild(style);
}

// Add mobile-specific styles
const mobileStyles = document.createElement('style');
mobileStyles.textContent = `
    /* Mobile-specific styles */
    @media (max-width: 768px) {
        .wy-nav-content {
            padding: 1.25rem !important;
        }
        
        .wy-nav-top {
            display: block !important;
            background-color: var(--bg-tertiary, #2c2c2c) !important;
            color: var(--text-primary, #e8eaed) !important;
        }
        
        .wy-nav-top a {
            color: var(--text-primary, #e8eaed) !important;
        }
        
        .mobile-nav-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 199;
        }
        
        body.nav-open .mobile-nav-overlay {
            display: block;
        }
        
        .mobile-submenu-toggle {
            background: none;
            border: none;
            color: var(--text-secondary, #9aa0a6);
            cursor: pointer;
            padding: 0.25rem;
            margin-left: 0.5rem;
            transition: transform 0.2s ease;
        }
        
        .mobile-submenu-toggle.open {
            transform: rotate(180deg);
        }
        
        .mobile-submenu-open > ul {
            display: block !important;
        }
        
        .table-responsive {
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            margin-bottom: 1rem;
        }
        
        .mobile-friendly-code {
            margin-left: -1.25rem !important;
            margin-right: -1.25rem !important;
            border-radius: 0 !important;
            border-left: none !important;
            border-right: none !important;
        }
        
        .mobile-friendly-code pre {
            padding: 1rem !important;
            font-size: 0.85rem !important;
        }
        
        .mobile-visible {
            opacity: 0.7 !important;
        }
        
        .math-wrapper {
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            margin-bottom: 1rem;
        }
        
        .on-this-page-fixed {
            margin-left: -1.25rem !important;
            margin-right: -1.25rem !important;
            border-radius: 0 !important;
            border-left: none !important;
            border-right: none !important;
        }
    }
`;
document.head.appendChild(mobileStyles); 