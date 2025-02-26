// Navigation Enhancer for memories-dev documentation
document.addEventListener('DOMContentLoaded', function() {
    // Enhance the navigation menu
    enhanceNavigation();
    
    // Add breadcrumbs
    addBreadcrumbs();
    
    // Add section navigation - removed as requested
    // addSectionNavigation();
    
    // Add back to top button
    addBackToTopButton();
});

/**
 * Enhance the navigation menu with collapsible sections and active highlighting
 */
function enhanceNavigation() {
    // Get the navigation menu
    const navMenu = document.querySelector('.wy-menu-vertical');
    if (!navMenu) return;
    
    // Add styles for enhanced navigation
    const style = document.createElement('style');
    style.textContent = `
        /* Navigation menu styling */
        .wy-menu-vertical {
            font-size: 15px;
        }
        
        .wy-menu-vertical a {
            padding: 10px 15px;
            transition: all 0.2s;
        }
        
        .wy-menu-vertical li.current > a {
            border-left: 4px solid var(--accent-color);
            padding-left: 11px;
            background-color: rgba(66, 133, 244, 0.1);
        }
        
        .wy-menu-vertical li.toctree-l1.current > a {
            border-bottom: 1px solid rgba(0, 0, 0, 0.05);
        }
        
        /* Collapsible sections */
        .wy-menu-vertical li.toctree-l1 {
            margin-bottom: 4px;
        }
        
        .wy-menu-vertical li.toctree-l1 > a {
            font-weight: 600;
            background-color: rgba(0, 0, 0, 0.03);
            border-radius: 4px;
        }
        
        .wy-menu-vertical li.toctree-l1 > a:hover {
            background-color: rgba(66, 133, 244, 0.1);
        }
        
        /* Section toggle button */
        .section-toggle {
            float: right;
            margin-right: 5px;
            transition: transform 0.3s;
            opacity: 0.7;
        }
        
        .section-toggle.collapsed {
            transform: rotate(-90deg);
        }
        
        /* Section content */
        .section-content {
            max-height: 1000px;
            overflow: hidden;
            transition: max-height 0.3s ease-in-out;
        }
        
        .section-content.collapsed {
            max-height: 0;
        }
        
        /* Improve nested navigation */
        .wy-menu-vertical li.toctree-l2 a,
        .wy-menu-vertical li.toctree-l3 a,
        .wy-menu-vertical li.toctree-l4 a {
            padding-left: 25px;
        }
        
        .wy-menu-vertical li.toctree-l3 a {
            padding-left: 35px;
        }
        
        .wy-menu-vertical li.toctree-l4 a {
            padding-left: 45px;
        }
        
        /* Active section highlighting */
        .wy-menu-vertical li.active-section > a {
            background-color: rgba(66, 133, 244, 0.1);
            color: var(--accent-color);
            font-weight: 600;
        }
    `;
    
    document.head.appendChild(style);
    
    // Add toggle buttons to top-level sections
    const topLevelItems = navMenu.querySelectorAll('li.toctree-l1');
    
    topLevelItems.forEach(function(item) {
        const link = item.querySelector('a');
        if (!link) return;
        
        // Create toggle button
        const toggleBtn = document.createElement('span');
        toggleBtn.className = 'section-toggle';
        toggleBtn.innerHTML = '▼';
        
        // Add toggle button to link
        link.appendChild(toggleBtn);
        
        // Get section content
        const sectionContent = item.querySelector('ul');
        if (!sectionContent) {
            toggleBtn.style.display = 'none';
            return;
        }
        
        // Check if section should be collapsed by default
        const isCurrentSection = item.classList.contains('current');
        if (!isCurrentSection) {
            toggleBtn.classList.add('collapsed');
            sectionContent.classList.add('collapsed');
        }
        
        // Add click event to toggle button
        link.addEventListener('click', function(e) {
            // Only toggle if clicking the toggle button or link text (not child links)
            if (e.target === toggleBtn || e.target === link) {
                e.preventDefault();
                
                // Toggle collapsed state
                toggleBtn.classList.toggle('collapsed');
                sectionContent.classList.toggle('collapsed');
            }
        });
    });
    
    // Highlight active section based on current page
    highlightActiveSection();
}

/**
 * Highlight the active section in the navigation menu
 */
function highlightActiveSection() {
    // Get current page path
    const currentPath = window.location.pathname;
    
    // Get all navigation links
    const navLinks = document.querySelectorAll('.wy-menu-vertical a');
    
    // Find the link that matches the current page
    navLinks.forEach(function(link) {
        const linkPath = link.getAttribute('href');
        
        // Check if link path is in current path
        if (currentPath.includes(linkPath) && linkPath !== '#') {
            // Add active class to parent li
            const parentLi = link.closest('li');
            if (parentLi) {
                parentLi.classList.add('active-section');
                
                // Expand parent sections
                let parent = parentLi.parentElement;
                while (parent) {
                    const parentLi = parent.closest('li');
                    if (!parentLi) break;
                    
                    // Remove collapsed class from parent section
                    const sectionContent = parentLi.querySelector('ul');
                    const toggleBtn = parentLi.querySelector('.section-toggle');
                    
                    if (sectionContent) {
                        sectionContent.classList.remove('collapsed');
                    }
                    
                    if (toggleBtn) {
                        toggleBtn.classList.remove('collapsed');
                    }
                    
                    parent = parentLi.parentElement;
                }
            }
        }
    });
}

/**
 * Add breadcrumbs to the page
 */
function addBreadcrumbs() {
    // Get the document title
    const docTitle = document.querySelector('.document h1');
    if (!docTitle) return;
    
    // Create breadcrumbs container
    const breadcrumbsContainer = document.createElement('div');
    breadcrumbsContainer.className = 'breadcrumbs';
    
    // Get breadcrumb items from navigation
    const breadcrumbItems = [];
    
    // Add home link
    breadcrumbItems.push({
        text: 'Home',
        href: '/index.html'
    });
    
    // Get current page path
    const currentPath = window.location.pathname;
    
    // Find active sections in navigation
    const activeItems = document.querySelectorAll('.wy-menu-vertical li.current');
    activeItems.forEach(function(item, index) {
        const link = item.querySelector('a');
        if (!link) return;
        
        // Skip the last item (current page)
        if (index < activeItems.length - 1) {
            breadcrumbItems.push({
                text: link.textContent.trim().replace('▼', ''),
                href: link.getAttribute('href')
            });
        }
    });
    
    // Add current page
    breadcrumbItems.push({
        text: docTitle.textContent.trim(),
        href: '#'
    });
    
    // Create breadcrumb elements
    breadcrumbItems.forEach(function(item, index) {
        // Create breadcrumb item
        const breadcrumbItem = document.createElement('span');
        
        // Add separator for all but first item
        if (index > 0) {
            const separator = document.createElement('span');
            separator.className = 'breadcrumb-separator';
            separator.textContent = ' / ';
            breadcrumbsContainer.appendChild(separator);
        }
        
        // Create link if not current page
        if (item.href !== '#') {
            const link = document.createElement('a');
            link.href = item.href;
            link.textContent = item.text;
            breadcrumbItem.appendChild(link);
        } else {
            breadcrumbItem.textContent = item.text;
            breadcrumbItem.className = 'breadcrumb-current';
        }
        
        breadcrumbsContainer.appendChild(breadcrumbItem);
    });
    
    // Add styles for breadcrumbs
    const style = document.createElement('style');
    style.textContent = `
        .breadcrumbs {
            margin-bottom: 1.5em;
            padding: 8px 12px;
            background-color: var(--primary-light);
            border-radius: 4px;
            font-size: 14px;
            color: var(--text-muted);
        }
        
        .breadcrumbs a {
            color: var(--accent-color);
            text-decoration: none;
        }
        
        .breadcrumbs a:hover {
            text-decoration: underline;
        }
        
        .breadcrumb-current {
            font-weight: 600;
            color: var(--text-color);
        }
        
        .breadcrumb-separator {
            color: var(--text-muted);
            margin: 0 4px;
        }
    `;
    
    document.head.appendChild(style);
    
    // Insert breadcrumbs before document title
    docTitle.parentNode.insertBefore(breadcrumbsContainer, docTitle);
}

/**
 * Add section navigation to the page
 */
function addSectionNavigation() {
    // Get the document content
    const docContent = document.querySelector('.document');
    if (!docContent) return;
    
    // Get all headings in the document
    const headings = docContent.querySelectorAll('h2, h3');
    if (headings.length < 3) return; // Only add section nav if there are enough headings
    
    // Create section navigation container
    const sectionNavContainer = document.createElement('div');
    sectionNavContainer.className = 'section-navigation';
    sectionNavContainer.innerHTML = '<h3>On This Page</h3>';
    
    // Create section navigation list
    const sectionNavList = document.createElement('ul');
    
    // Add headings to section navigation
    headings.forEach(function(heading) {
        // Add ID to heading if it doesn't have one
        if (!heading.id) {
            heading.id = heading.textContent.trim().toLowerCase().replace(/\s+/g, '-');
        }
        
        // Create list item
        const listItem = document.createElement('li');
        listItem.className = heading.tagName.toLowerCase() === 'h3' ? 'section-nav-subsection' : '';
        
        // Create link
        const link = document.createElement('a');
        link.href = `#${heading.id}`;
        link.textContent = heading.textContent.trim();
        
        // Add click event for smooth scrolling
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                // Smooth scroll to target
                window.scrollTo({
                    top: targetElement.offsetTop - 20,
                    behavior: 'smooth'
                });
                
                // Update URL hash
                history.pushState(null, null, `#${targetId}`);
            }
        });
        
        listItem.appendChild(link);
        sectionNavList.appendChild(listItem);
    });
    
    sectionNavContainer.appendChild(sectionNavList);
    
    // Add styles for section navigation
    const style = document.createElement('style');
    style.textContent = `
        .section-navigation {
            position: sticky;
            top: 20px;
            float: right;
            width: 250px;
            margin-left: 30px;
            margin-bottom: 20px;
            padding: 15px;
            background-color: var(--primary-light);
            border-radius: 4px;
            font-size: 14px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
        }
        
        .section-navigation h3 {
            margin-top: 0;
            margin-bottom: 10px;
            font-size: 16px;
            color: var(--text-color);
        }
        
        .section-navigation ul {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .section-navigation li {
            margin-bottom: 8px;
            line-height: 1.3;
        }
        
        .section-navigation li.section-nav-subsection {
            padding-left: 15px;
            font-size: 13px;
        }
        
        .section-navigation a {
            color: var(--text-color);
            text-decoration: none;
            display: block;
            transition: color 0.2s;
        }
        
        .section-navigation a:hover {
            color: var(--accent-color);
        }
        
        .section-navigation a.active {
            color: var(--accent-color);
            font-weight: 600;
        }
        
        /* Responsive styles */
        @media (max-width: 992px) {
            .section-navigation {
                float: none;
                width: auto;
                margin-left: 0;
                margin-bottom: 30px;
            }
        }
    `;
    
    document.head.appendChild(style);
    
    // Insert section navigation at the beginning of the document
    const firstParagraph = docContent.querySelector('p');
    if (firstParagraph) {
        firstParagraph.parentNode.insertBefore(sectionNavContainer, firstParagraph);
    } else {
        const docBody = docContent.querySelector('.body');
        if (docBody) {
            docBody.insertBefore(sectionNavContainer, docBody.firstChild);
        }
    }
    
    // Highlight active section on scroll
    window.addEventListener('scroll', function() {
        // Get all headings with IDs
        const headingsWithIds = Array.from(docContent.querySelectorAll('h2[id], h3[id]'));
        
        // Find the heading that is currently in view
        let activeHeading = null;
        
        for (let i = 0; i < headingsWithIds.length; i++) {
            const heading = headingsWithIds[i];
            const rect = heading.getBoundingClientRect();
            
            // Check if heading is in view
            if (rect.top <= 100) {
                activeHeading = heading;
            } else {
                break;
            }
        }
        
        // Highlight active section in navigation
        if (activeHeading) {
            const activeLink = sectionNavContainer.querySelector(`a[href="#${activeHeading.id}"]`);
            
            // Remove active class from all links
            sectionNavContainer.querySelectorAll('a').forEach(function(link) {
                link.classList.remove('active');
            });
            
            // Add active class to current link
            if (activeLink) {
                activeLink.classList.add('active');
            }
        }
    });
}

/**
 * Add back to top button
 */
function addBackToTopButton() {
    // Create back to top button
    const backToTopBtn = document.createElement('button');
    backToTopBtn.className = 'back-to-top';
    backToTopBtn.innerHTML = '↑';
    backToTopBtn.setAttribute('aria-label', 'Back to top');
    backToTopBtn.setAttribute('title', 'Back to top');
    
    // Add styles for back to top button
    const style = document.createElement('style');
    style.textContent = `
        .back-to-top {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background-color: var(--accent-color);
            color: white;
            border: none;
            font-size: 20px;
            cursor: pointer;
            opacity: 0;
            transform: translateY(20px);
            transition: opacity 0.3s, transform 0.3s;
            z-index: 1000;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
        }
        
        .back-to-top:hover {
            background-color: var(--accent-dark);
        }
        
        .back-to-top.visible {
            opacity: 1;
            transform: translateY(0);
        }
        
        @media (max-width: 768px) {
            .back-to-top {
                bottom: 20px;
                right: 20px;
                width: 36px;
                height: 36px;
                font-size: 18px;
            }
        }
    `;
    
    document.head.appendChild(style);
    
    // Add button to body
    document.body.appendChild(backToTopBtn);
    
    // Add click event to scroll to top
    backToTopBtn.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
    
    // Show/hide button on scroll
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTopBtn.classList.add('visible');
        } else {
            backToTopBtn.classList.remove('visible');
        }
    });
} 