// Navigation enhancer for a book-like experience
document.addEventListener('DOMContentLoaded', function() {
    // Add keyboard navigation
    setupKeyboardNavigation();
    
    // Enhance table of contents
    enhanceTOC();
    
    // Add page turning animation
    addPageTurningEffect();
    
    // Remember last visited page
    trackLastVisitedPage();
});

/**
 * Set up keyboard navigation for moving between pages
 */
function setupKeyboardNavigation() {
    document.addEventListener('keydown', function(e) {
        // Only respond to keyboard shortcuts if we're not in an input field
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) {
            return;
        }
        
        // Left arrow (←) for previous page
        if (e.key === 'ArrowLeft' || e.keyCode === 37) {
            const prevLink = document.querySelector('a.prev');
            if (prevLink) {
                e.preventDefault();
                window.location.href = prevLink.href;
            }
        }
        
        // Right arrow (→) for next page
        if (e.key === 'ArrowRight' || e.keyCode === 39) {
            const nextLink = document.querySelector('a.next');
            if (nextLink) {
                e.preventDefault();
                window.location.href = nextLink.href;
            }
        }
        
        // Home key for index page
        if (e.key === 'Home') {
            const homeLink = document.querySelector('a.icon-home');
            if (homeLink) {
                e.preventDefault();
                window.location.href = homeLink.href;
            }
        }
        
        // 't' for scrolling to top of page
        if (e.key === 't' || e.keyCode === 84) {
            e.preventDefault();
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        }
        
        // 'b' for scrolling to bottom of page
        if (e.key === 'b' || e.keyCode === 66) {
            e.preventDefault();
            window.scrollTo({
                top: document.body.scrollHeight,
                behavior: 'smooth'
            });
        }
    });
    
    // Add keyboard shortcut hints
    addKeyboardShortcutHints();
}

/**
 * Add visual keyboard shortcut hints to the UI
 */
function addKeyboardShortcutHints() {
    // Add to navigation links
    const prevLink = document.querySelector('a.prev');
    const nextLink = document.querySelector('a.next');
    
    if (prevLink) {
        const prevHint = document.createElement('span');
        prevHint.className = 'keyboard-hint';
        prevHint.textContent = '←';
        prevHint.title = 'Keyboard shortcut: Left Arrow';
        prevHint.style.marginLeft = '5px';
        prevHint.style.opacity = '0.7';
        prevHint.style.fontSize = '0.8em';
        prevLink.appendChild(prevHint);
    }
    
    if (nextLink) {
        const nextHint = document.createElement('span');
        nextHint.className = 'keyboard-hint';
        nextHint.textContent = '→';
        nextHint.title = 'Keyboard shortcut: Right Arrow';
        nextHint.style.marginLeft = '5px';
        nextHint.style.opacity = '0.7';
        nextHint.style.fontSize = '0.8em';
        nextLink.appendChild(nextHint);
    }
    
    // Create a keyboard shortcuts help button
    const helpButton = document.createElement('button');
    helpButton.className = 'keyboard-help-btn';
    helpButton.textContent = '⌨️';
    helpButton.title = 'Keyboard Shortcuts';
    helpButton.style.position = 'fixed';
    helpButton.style.bottom = '20px';
    helpButton.style.right = '20px';
    helpButton.style.zIndex = '1000';
    helpButton.style.padding = '10px';
    helpButton.style.borderRadius = '50%';
    helpButton.style.backgroundColor = '#f8f9fa';
    helpButton.style.border = '1px solid #e1e4e8';
    helpButton.style.cursor = 'pointer';
    helpButton.style.boxShadow = '0 1px 2px rgba(0, 0, 0, 0.1)';
    
    helpButton.addEventListener('click', function() {
        showKeyboardShortcutsModal();
    });
    
    document.body.appendChild(helpButton);
}

/**
 * Display a modal with all keyboard shortcuts
 */
function showKeyboardShortcutsModal() {
    // Create modal container
    const modal = document.createElement('div');
    modal.className = 'keyboard-shortcuts-modal';
    modal.style.position = 'fixed';
    modal.style.top = '0';
    modal.style.left = '0';
    modal.style.width = '100%';
    modal.style.height = '100%';
    modal.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
    modal.style.zIndex = '2000';
    modal.style.display = 'flex';
    modal.style.justifyContent = 'center';
    modal.style.alignItems = 'center';
    
    // Create modal content
    const content = document.createElement('div');
    content.style.backgroundColor = '#fff';
    content.style.padding = '20px';
    content.style.borderRadius = '5px';
    content.style.maxWidth = '500px';
    content.style.width = '80%';
    content.style.maxHeight = '80vh';
    content.style.overflow = 'auto';
    content.style.boxShadow = '0 3px 6px rgba(0, 0, 0, 0.16)';
    
    // Add title
    const title = document.createElement('h3');
    title.textContent = 'Keyboard Shortcuts';
    title.style.marginTop = '0';
    
    // Create shortcut list
    const list = document.createElement('table');
    list.style.width = '100%';
    list.style.borderCollapse = 'collapse';
    
    // Add shortcuts
    const shortcuts = [
        ['←', 'Previous page'],
        ['→', 'Next page'],
        ['Home', 'Go to index page'],
        ['t', 'Scroll to top of page'],
        ['b', 'Scroll to bottom of page'],
        ['Esc', 'Close this dialog']
    ];
    
    shortcuts.forEach(function(shortcut) {
        const row = document.createElement('tr');
        
        const keyCell = document.createElement('td');
        keyCell.style.padding = '8px';
        keyCell.style.borderBottom = '1px solid #eee';
        
        const keySpan = document.createElement('span');
        keySpan.style.backgroundColor = '#f6f8fa';
        keySpan.style.border = '1px solid #d1d5da';
        keySpan.style.borderRadius = '3px';
        keySpan.style.padding = '3px 6px';
        keySpan.style.fontFamily = 'monospace';
        keySpan.textContent = shortcut[0];
        
        keyCell.appendChild(keySpan);
        
        const descCell = document.createElement('td');
        descCell.style.padding = '8px';
        descCell.style.borderBottom = '1px solid #eee';
        descCell.textContent = shortcut[1];
        
        row.appendChild(keyCell);
        row.appendChild(descCell);
        list.appendChild(row);
    });
    
    // Add close button
    const closeButton = document.createElement('button');
    closeButton.textContent = 'Close';
    closeButton.style.marginTop = '20px';
    closeButton.style.padding = '8px 16px';
    closeButton.style.backgroundColor = '#f6f8fa';
    closeButton.style.border = '1px solid #d1d5da';
    closeButton.style.borderRadius = '3px';
    closeButton.style.cursor = 'pointer';
    
    closeButton.addEventListener('click', function() {
        document.body.removeChild(modal);
    });
    
    // Add Escape key to close modal
    modal.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' || e.keyCode === 27) {
            document.body.removeChild(modal);
        }
    });
    
    // Assemble modal
    content.appendChild(title);
    content.appendChild(list);
    content.appendChild(closeButton);
    modal.appendChild(content);
    
    // Close when clicking outside the content
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            document.body.removeChild(modal);
        }
    });
    
    document.body.appendChild(modal);
    
    // Focus the modal for keyboard events
    modal.setAttribute('tabindex', '-1');
    modal.focus();
}

/**
 * Enhance the table of contents with collapsible sections and highlighting
 */
function enhanceTOC() {
    const toc = document.querySelector('.toctree-wrapper') || document.querySelector('.toc');
    
    if (!toc) return;
    
    // Add collapsible functionality to TOC sections
    const tocItems = toc.querySelectorAll('li.toctree-l1');
    
    tocItems.forEach(function(item) {
        const link = item.querySelector('a');
        const sublist = item.querySelector('ul');
        
        if (sublist && link) {
            // Add toggle button
            const toggleBtn = document.createElement('span');
            toggleBtn.className = 'toc-toggle';
            toggleBtn.innerHTML = '▶';
            toggleBtn.style.cursor = 'pointer';
            toggleBtn.style.marginRight = '5px';
            toggleBtn.style.fontSize = '0.8em';
            toggleBtn.style.transition = 'transform 0.2s';
            
            // Check if this section contains the current page
            const isCurrentSection = sublist.querySelector('a.current') !== null;
            
            // Initially collapse sections that don't contain current page
            if (!isCurrentSection) {
                sublist.style.display = 'none';
            } else {
                toggleBtn.innerHTML = '▼';
                toggleBtn.style.transform = 'rotate(90deg)';
            }
            
            // Add click handler
            toggleBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                if (sublist.style.display === 'none') {
                    sublist.style.display = '';
                    toggleBtn.innerHTML = '▼';
                    toggleBtn.style.transform = 'rotate(90deg)';
                } else {
                    sublist.style.display = 'none';
                    toggleBtn.innerHTML = '▶';
                    toggleBtn.style.transform = '';
                }
            });
            
            // Insert the toggle button before the link
            link.parentNode.insertBefore(toggleBtn, link);
        }
    });
    
    // Highlight current section
    const currentLink = toc.querySelector('a.current');
    if (currentLink) {
        currentLink.parentNode.style.backgroundColor = 'rgba(41, 128, 185, 0.1)';
        currentLink.parentNode.style.borderLeft = '3px solid #2980b9';
        currentLink.parentNode.style.paddingLeft = '5px';
    }
}

/**
 * Add a subtle page turning effect when navigating
 */
function addPageTurningEffect() {
    // Add CSS for page turning effect
    const styleEl = document.createElement('style');
    styleEl.textContent = `
        @keyframes pageTurnIn {
            from { opacity: 0; transform: translateX(20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        @keyframes pageTurnOut {
            from { opacity: 1; transform: translateX(0); }
            to { opacity: 0; transform: translateX(-20px); }
        }
        
        .page-turn-in {
            animation: pageTurnIn 0.3s ease-out;
        }
    `;
    document.head.appendChild(styleEl);
    
    // Add animation to current page
    const mainContent = document.querySelector('.document') || document.querySelector('article') || document.querySelector('main');
    if (mainContent) {
        mainContent.classList.add('page-turn-in');
    }
    
    // Add animation when leaving page
    document.addEventListener('click', function(e) {
        const target = e.target.closest('a');
        if (target && target.href && target.href.startsWith(window.location.origin) && !target.href.includes('#')) {
            // It's an internal link, apply the animation
            if (mainContent) {
                e.preventDefault();
                
                mainContent.style.animation = 'pageTurnOut 0.3s ease-in forwards';
                
                setTimeout(function() {
                    window.location.href = target.href;
                }, 300);
            }
        }
    });
}

/**
 * Track the last visited page for returning visitors
 */
function trackLastVisitedPage() {
    // Store the current page as the last visited page
    if (typeof localStorage !== 'undefined') {
        try {
            localStorage.setItem('lastVisitedPage', window.location.pathname);
        } catch (e) {
            console.warn('Unable to store last visited page: ', e);
        }
    }
    
    // Add a "Continue reading" button if there's a stored page
    const storedPage = localStorage.getItem('lastVisitedPage');
    if (storedPage && storedPage !== window.location.pathname && !document.querySelector('.continue-reading')) {
        // Find the title of the last visited page
        let pageTitle = 'where you left off';
        
        // Try to find the page title from the navigation links
        const navLinks = document.querySelectorAll('.toctree-l1 a, .toctree-l2 a, .toctree-l3 a');
        navLinks.forEach(link => {
            if (link.getAttribute('href') && storedPage.endsWith(link.getAttribute('href'))) {
                pageTitle = link.textContent.trim();
            }
        });
        
        // Create continue reading button
        const continueBtn = document.createElement('div');
        continueBtn.className = 'continue-reading';
        continueBtn.style.position = 'fixed';
        continueBtn.style.bottom = '70px';
        continueBtn.style.right = '20px';
        continueBtn.style.backgroundColor = '#2980b9';
        continueBtn.style.color = 'white';
        continueBtn.style.padding = '10px 15px';
        continueBtn.style.borderRadius = '5px';
        continueBtn.style.cursor = 'pointer';
        continueBtn.style.boxShadow = '0 2px 5px rgba(0, 0, 0, 0.2)';
        continueBtn.style.zIndex = '1000';
        continueBtn.style.fontSize = '14px';
        continueBtn.innerHTML = `<i class="fa fa-book"></i> Continue Reading: <strong>${pageTitle}</strong>`;
        
        continueBtn.addEventListener('click', function() {
            window.location.href = storedPage;
        });
        
        // Add a close button
        const closeBtn = document.createElement('span');
        closeBtn.innerHTML = '&times;';
        closeBtn.style.marginLeft = '10px';
        closeBtn.style.fontWeight = 'bold';
        closeBtn.style.fontSize = '16px';
        
        closeBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            document.body.removeChild(continueBtn);
        });
        
        continueBtn.appendChild(closeBtn);
        
        // Add to the page
        setTimeout(function() {
            document.body.appendChild(continueBtn);
        }, 2000); // Add after a short delay
    }
} 