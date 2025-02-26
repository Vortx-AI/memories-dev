// Progress Tracker for memories-dev documentation tutorials
document.addEventListener('DOMContentLoaded', function() {
    // Initialize progress tracker
    initializeProgressTracker();
});

/**
 * Initialize the progress tracker component
 */
function initializeProgressTracker() {
    // Check if we're on a tutorial page
    if (isTutorialPage()) {
        // Add progress tracker to the page
        addProgressTracker();
        
        // Add styles for progress tracker
        addProgressTrackerStyles();
        
        // Initialize progress state
        initializeProgressState();
    }
}

/**
 * Check if current page is a tutorial page
 * @returns {boolean} - True if current page is a tutorial
 */
function isTutorialPage() {
    // Check URL path for tutorial indicators
    const path = window.location.pathname;
    return (
        path.includes('/getting_started/') ||
        path.includes('/examples/') ||
        path.includes('/tutorials/') ||
        document.querySelector('.tutorial-content') !== null
    );
}

/**
 * Add progress tracker to the page
 */
function addProgressTracker() {
    // Create progress tracker container
    const trackerContainer = document.createElement('div');
    trackerContainer.className = 'progress-tracker-container';
    trackerContainer.setAttribute('aria-label', 'Tutorial progress');
    
    // Create progress header
    const trackerHeader = document.createElement('div');
    trackerHeader.className = 'progress-tracker-header';
    
    const trackerTitle = document.createElement('h3');
    trackerTitle.textContent = 'Tutorial Progress';
    
    const trackerToggle = document.createElement('button');
    trackerToggle.className = 'progress-tracker-toggle';
    trackerToggle.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M1.646 4.646a.5.5 0 0 1 .708 0L8 10.293l5.646-5.647a.5.5 0 0 1 .708.708l-6 6a.5.5 0 0 1-.708 0l-6-6a.5.5 0 0 1 0-.708z"/></svg>';
    trackerToggle.setAttribute('aria-expanded', 'true');
    trackerToggle.setAttribute('aria-controls', 'progress-tracker-content');
    
    trackerHeader.appendChild(trackerTitle);
    trackerHeader.appendChild(trackerToggle);
    
    // Create progress content
    const trackerContent = document.createElement('div');
    trackerContent.className = 'progress-tracker-content';
    trackerContent.id = 'progress-tracker-content';
    
    // Create progress steps
    const steps = createProgressSteps();
    trackerContent.appendChild(steps);
    
    // Create progress actions
    const trackerActions = document.createElement('div');
    trackerActions.className = 'progress-tracker-actions';
    
    const markCompleteButton = document.createElement('button');
    markCompleteButton.className = 'progress-mark-complete';
    markCompleteButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg> Mark as Complete';
    
    const resetProgressButton = document.createElement('button');
    resetProgressButton.className = 'progress-reset';
    resetProgressButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"/><path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"/></svg> Reset Progress';
    
    trackerActions.appendChild(markCompleteButton);
    trackerActions.appendChild(resetProgressButton);
    
    trackerContent.appendChild(trackerActions);
    
    // Assemble tracker
    trackerContainer.appendChild(trackerHeader);
    trackerContainer.appendChild(trackerContent);
    
    // Add to page
    const contentArea = document.querySelector('.wy-nav-content');
    if (contentArea) {
        // Insert at the top of the content area
        contentArea.insertBefore(trackerContainer, contentArea.firstChild);
    }
    
    // Add event listeners
    trackerToggle.addEventListener('click', function() {
        trackerContent.classList.toggle('collapsed');
        const isExpanded = !trackerContent.classList.contains('collapsed');
        trackerToggle.setAttribute('aria-expanded', isExpanded.toString());
        trackerToggle.classList.toggle('collapsed');
        
        // Save state in localStorage
        localStorage.setItem('progress_tracker_expanded', isExpanded.toString());
    });
    
    markCompleteButton.addEventListener('click', function() {
        markCurrentPageComplete();
    });
    
    resetProgressButton.addEventListener('click', function() {
        resetTutorialProgress();
    });
    
    // Restore expanded/collapsed state
    const isExpanded = localStorage.getItem('progress_tracker_expanded');
    if (isExpanded === 'false') {
        trackerContent.classList.add('collapsed');
        trackerToggle.setAttribute('aria-expanded', 'false');
        trackerToggle.classList.add('collapsed');
    }
}

/**
 * Create progress steps based on tutorial structure
 * @returns {HTMLElement} - The progress steps element
 */
function createProgressSteps() {
    const stepsContainer = document.createElement('div');
    stepsContainer.className = 'progress-steps';
    
    // Get tutorial structure
    const tutorialStructure = getTutorialStructure();
    
    // Create steps
    tutorialStructure.forEach((step, index) => {
        const stepElement = document.createElement('div');
        stepElement.className = 'progress-step';
        stepElement.dataset.page = step.page;
        
        // Check if current page
        if (isCurrentPage(step.page)) {
            stepElement.classList.add('current');
        }
        
        // Create step number
        const stepNumber = document.createElement('div');
        stepNumber.className = 'step-number';
        stepNumber.textContent = (index + 1).toString();
        
        // Create step content
        const stepContent = document.createElement('div');
        stepContent.className = 'step-content';
        
        const stepTitle = document.createElement('div');
        stepTitle.className = 'step-title';
        
        const stepLink = document.createElement('a');
        stepLink.href = step.page;
        stepLink.textContent = step.title;
        
        stepTitle.appendChild(stepLink);
        stepContent.appendChild(stepTitle);
        
        // Create step status
        const stepStatus = document.createElement('div');
        stepStatus.className = 'step-status';
        
        const completeIcon = document.createElement('span');
        completeIcon.className = 'status-complete';
        completeIcon.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/></svg>';
        
        const incompleteIcon = document.createElement('span');
        incompleteIcon.className = 'status-incomplete';
        incompleteIcon.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM8 4a.905.905 0 0 0-.9.995l.35 3.507a.552.552 0 0 0 1.1 0l.35-3.507A.905.905 0 0 0 8 4zm.002 6a1 1 0 1 0 0 2 1 1 0 0 0 0-2z"/></svg>';
        
        stepStatus.appendChild(completeIcon);
        stepStatus.appendChild(incompleteIcon);
        
        // Assemble step
        stepElement.appendChild(stepNumber);
        stepElement.appendChild(stepContent);
        stepElement.appendChild(stepStatus);
        
        stepsContainer.appendChild(stepElement);
    });
    
    return stepsContainer;
}

/**
 * Get tutorial structure
 * @returns {Array} - Array of tutorial steps
 */
function getTutorialStructure() {
    // Try to get structure from page metadata
    const metaStructure = document.querySelector('meta[name="tutorial-structure"]');
    if (metaStructure) {
        try {
            return JSON.parse(metaStructure.getAttribute('content'));
        } catch (e) {
            console.error('Error parsing tutorial structure:', e);
            // Return empty array to prevent loop
            return [];
        }
    }
    
    // Fallback: Try to extract from table of contents
    const tocLinks = document.querySelectorAll('.wy-menu-vertical li.toctree-l1.current li.toctree-l2 a');
    if (tocLinks.length > 0) {
        // Limit to maximum 20 links to prevent excessive nesting
        return Array.from(tocLinks).slice(0, 20).map(link => ({
            title: link.textContent.trim(),
            page: link.getAttribute('href')
        }));
    }
    
    // Fallback: Try to extract from breadcrumbs
    const breadcrumbs = document.querySelectorAll('.wy-breadcrumbs li');
    if (breadcrumbs.length > 1) {
        const parentLink = breadcrumbs[breadcrumbs.length - 2].querySelector('a');
        if (parentLink) {
            const parentUrl = parentLink.getAttribute('href');
            const parentDir = parentUrl.substring(0, parentUrl.lastIndexOf('/') + 1);
            
            // Try to find sibling pages - only include if they exist
            const currentPage = window.location.pathname;
            // Prevent loops by checking if current page is already in the structure
            return [
                { title: 'Parent Page', page: parentUrl },
                { title: 'Current Page', page: currentPage }
            ];
        }
    }
    
    // Last fallback: Just use current page
    return [
        { title: document.title, page: window.location.pathname }
    ];
}

/**
 * Check if the given page is the current page
 * @param {string} page - The page path to check
 * @returns {boolean} - True if the given page is the current page
 */
function isCurrentPage(page) {
    const currentPath = window.location.pathname;
    const pagePath = page.startsWith('/') ? page : `/${page}`;
    
    return currentPath.endsWith(pagePath) || 
           currentPath === pagePath || 
           currentPath.endsWith(page);
}

/**
 * Initialize progress state
 */
function initializeProgressState() {
    // Get completed pages from localStorage
    const completedPages = getCompletedPages();
    
    // Update UI to reflect completed pages
    updateProgressUI(completedPages);
    
    // Check if current page is already completed
    const currentPage = window.location.pathname;
    const isCompleted = completedPages.includes(currentPage);
    
    // Update mark complete button
    const markCompleteButton = document.querySelector('.progress-mark-complete');
    if (markCompleteButton) {
        if (isCompleted) {
            markCompleteButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg> Completed';
            markCompleteButton.classList.add('completed');
        } else {
            markCompleteButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg> Mark as Complete';
            markCompleteButton.classList.remove('completed');
        }
    }
}

/**
 * Get completed pages from localStorage
 * @returns {Array} - Array of completed page paths
 */
function getCompletedPages() {
    const completedPagesJson = localStorage.getItem('tutorial_completed_pages');
    return completedPagesJson ? JSON.parse(completedPagesJson) : [];
}

/**
 * Update progress UI based on completed pages
 * @param {Array} completedPages - Array of completed page paths
 */
function updateProgressUI(completedPages) {
    // Update step status
    const steps = document.querySelectorAll('.progress-step');
    steps.forEach(step => {
        const stepPage = step.dataset.page;
        const isCompleted = completedPages.some(page => 
            page.endsWith(stepPage) || page === stepPage
        );
        
        if (isCompleted) {
            step.classList.add('completed');
        } else {
            step.classList.remove('completed');
        }
    });
    
    // Update progress percentage
    const totalSteps = steps.length;
    const completedSteps = document.querySelectorAll('.progress-step.completed').length;
    const progressPercentage = totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0;
    
    // Update progress bar if it exists
    const progressBar = document.querySelector('.progress-bar-fill');
    if (progressBar) {
        progressBar.style.width = `${progressPercentage}%`;
    }
    
    // Update progress text
    const progressText = document.querySelector('.progress-tracker-header h3');
    if (progressText) {
        progressText.textContent = `Tutorial Progress: ${progressPercentage}%`;
    }
}

/**
 * Mark current page as complete
 */
function markCurrentPageComplete() {
    const currentPage = window.location.pathname;
    const completedPages = getCompletedPages();
    
    // Check if already completed
    const isCompleted = completedPages.includes(currentPage);
    
    if (isCompleted) {
        // Remove from completed pages
        const updatedPages = completedPages.filter(page => page !== currentPage);
        localStorage.setItem('tutorial_completed_pages', JSON.stringify(updatedPages));
        
        // Update UI
        updateProgressUI(updatedPages);
        
        // Update button
        const markCompleteButton = document.querySelector('.progress-mark-complete');
        if (markCompleteButton) {
            markCompleteButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg> Mark as Complete';
            markCompleteButton.classList.remove('completed');
        }
    } else {
        // Add to completed pages
        completedPages.push(currentPage);
        localStorage.setItem('tutorial_completed_pages', JSON.stringify(completedPages));
        
        // Update UI
        updateProgressUI(completedPages);
        
        // Update button
        const markCompleteButton = document.querySelector('.progress-mark-complete');
        if (markCompleteButton) {
            markCompleteButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg> Completed';
            markCompleteButton.classList.add('completed');
        }
        
        // Show completion message
        showCompletionMessage();
    }
}

/**
 * Show completion message
 */
function showCompletionMessage() {
    // Create message container
    const messageContainer = document.createElement('div');
    messageContainer.className = 'completion-message';
    
    // Create message content
    messageContainer.innerHTML = `
        <div class="completion-message-content">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
            </svg>
            <span>Page marked as complete!</span>
        </div>
    `;
    
    // Add to body
    document.body.appendChild(messageContainer);
    
    // Auto-remove after 3 seconds
    setTimeout(function() {
        if (document.body.contains(messageContainer)) {
            messageContainer.classList.add('hiding');
            
            // Remove after animation completes
            setTimeout(function() {
                if (document.body.contains(messageContainer)) {
                    messageContainer.remove();
                }
            }, 300);
        }
    }, 3000);
}

/**
 * Reset tutorial progress
 */
function resetTutorialProgress() {
    // Show confirmation dialog
    if (confirm('Are you sure you want to reset your progress for all tutorials?')) {
        // Clear completed pages
        localStorage.removeItem('tutorial_completed_pages');
        
        // Update UI
        updateProgressUI([]);
        
        // Update button
        const markCompleteButton = document.querySelector('.progress-mark-complete');
        if (markCompleteButton) {
            markCompleteButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg> Mark as Complete';
            markCompleteButton.classList.remove('completed');
        }
    }
}

/**
 * Add styles for progress tracker
 */
function addProgressTrackerStyles() {
    const style = document.createElement('style');
    style.textContent = `
        /* Progress Tracker Container */
        .progress-tracker-container {
            margin-bottom: 2rem;
            border-radius: 8px;
            background-color: var(--primary-light, #f8f9fa);
            border: 1px solid var(--border-color, #dadce0);
            overflow: hidden;
        }
        
        /* Progress Tracker Header */
        .progress-tracker-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem;
            background-color: var(--accent-color, #4285f4);
            color: white;
        }
        
        .progress-tracker-header h3 {
            margin: 0;
            font-size: 16px;
            font-weight: 500;
        }
        
        .progress-tracker-toggle {
            background: none;
            border: none;
            color: white;
            cursor: pointer;
            padding: 0.25rem;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s;
        }
        
        .progress-tracker-toggle.collapsed {
            transform: rotate(-90deg);
        }
        
        /* Progress Tracker Content */
        .progress-tracker-content {
            max-height: 500px;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }
        
        .progress-tracker-content.collapsed {
            max-height: 0;
        }
        
        /* Progress Steps */
        .progress-steps {
            padding: 1rem;
        }
        
        .progress-step {
            display: flex;
            align-items: flex-start;
            margin-bottom: 1rem;
            position: relative;
        }
        
        .progress-step:last-child {
            margin-bottom: 0;
        }
        
        .progress-step::before {
            content: '';
            position: absolute;
            top: 24px;
            left: 12px;
            bottom: -24px;
            width: 2px;
            background-color: var(--border-color, #dadce0);
            z-index: 1;
        }
        
        .progress-step:last-child::before {
            display: none;
        }
        
        .progress-step.completed::before {
            background-color: var(--success-color, #34a853);
        }
        
        .step-number {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background-color: var(--border-color, #dadce0);
            color: var(--text-color, #202124);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: bold;
            margin-right: 12px;
            flex-shrink: 0;
            z-index: 2;
        }
        
        .progress-step.current .step-number {
            background-color: var(--accent-color, #4285f4);
            color: white;
        }
        
        .progress-step.completed .step-number {
            background-color: var(--success-color, #34a853);
            color: white;
        }
        
        .step-content {
            flex: 1;
            padding-top: 2px;
        }
        
        .step-title {
            font-weight: 500;
            margin-bottom: 4px;
            color: var(--text-color, #202124);
        }
        
        .step-title a {
            color: inherit;
            text-decoration: none;
        }
        
        .step-title a:hover {
            text-decoration: underline;
            color: var(--accent-color, #4285f4);
        }
        
        .progress-step.current .step-title {
            color: var(--accent-color, #4285f4);
            font-weight: 600;
        }
        
        .step-status {
            margin-left: 12px;
            display: flex;
            align-items: center;
        }
        
        .status-complete {
            display: none;
            color: var(--success-color, #34a853);
        }
        
        .status-incomplete {
            display: block;
            color: var(--text-muted, #9aa0a6);
        }
        
        .progress-step.completed .status-complete {
            display: block;
        }
        
        .progress-step.completed .status-incomplete {
            display: none;
        }
        
        /* Progress Actions */
        .progress-tracker-actions {
            display: flex;
            justify-content: space-between;
            padding: 1rem;
            border-top: 1px solid var(--border-color, #dadce0);
            background-color: rgba(0, 0, 0, 0.02);
        }
        
        .progress-mark-complete,
        .progress-reset {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 500;
            font-size: 14px;
            transition: all 0.2s;
        }
        
        .progress-mark-complete {
            background-color: var(--accent-color, #4285f4);
            color: white;
            border: none;
        }
        
        .progress-mark-complete:hover {
            background-color: var(--accent-dark, #3367d6);
        }
        
        .progress-mark-complete.completed {
            background-color: var(--success-color, #34a853);
        }
        
        .progress-mark-complete.completed:hover {
            background-color: #2d9348;
        }
        
        .progress-reset {
            background-color: transparent;
            color: var(--text-color, #202124);
            border: 1px solid var(--border-color, #dadce0);
        }
        
        .progress-reset:hover {
            background-color: var(--primary-dark, #e9ecef);
        }
        
        /* Completion Message */
        .completion-message {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 1000;
            background-color: var(--success-color, #34a853);
            color: white;
            border-radius: 4px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
            opacity: 1;
            transition: opacity 0.3s;
        }
        
        .completion-message.hiding {
            opacity: 0;
        }
        
        .completion-message-content {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 12px 20px;
        }
        
        /* Responsive styles */
        @media (max-width: 768px) {
            .progress-tracker-actions {
                flex-direction: column;
                gap: 8px;
            }
            
            .progress-mark-complete,
            .progress-reset {
                width: 100%;
                justify-content: center;
            }
        }
    `;
    
    document.head.appendChild(style);
}

// Progress tracker for documentation reading
document.addEventListener('DOMContentLoaded', function() {
    // Create a progress bar element
    const progressBar = document.createElement('div');
    progressBar.id = 'reading-progress';
    progressBar.style.position = 'fixed';
    progressBar.style.top = '0';
    progressBar.style.left = '0';
    progressBar.style.height = '3px';
    progressBar.style.backgroundColor = '#2980b9';
    progressBar.style.width = '0%';
    progressBar.style.zIndex = '1000';
    progressBar.style.transition = 'width 0.2s ease-out';
    document.body.appendChild(progressBar);

    // Function to update progress based on scroll position
    function updateProgress() {
        // Get content area - use main content container in Sphinx
        const content = document.querySelector('.document') || document.querySelector('.body') || document.body;
        
        // Calculate how far the user has scrolled
        const scrollPosition = window.scrollY;
        const scrollHeight = content.scrollHeight - window.innerHeight;
        
        // Calculate the percentage scrolled and set the progress bar width
        if (scrollHeight > 0) {
            const scrollPercentage = (scrollPosition / scrollHeight) * 100;
            progressBar.style.width = scrollPercentage + '%';
            
            // Store progress in localStorage for this page
            if (typeof localStorage !== 'undefined') {
                try {
                    const currentPage = window.location.pathname;
                    localStorage.setItem('readingProgress-' + currentPage, scrollPercentage);
                    
                    // Create last read indicator
                    updateLastReadIndicator(currentPage, scrollPercentage);
                } catch (e) {
                    // Handle localStorage errors (e.g., private browsing mode)
                    console.warn('Unable to store reading progress: ', e);
                }
            }
        }
    }
    
    // Update last read indicator in the sidebar
    function updateLastReadIndicator(page, percentage) {
        // Get all navigation links
        const navLinks = document.querySelectorAll('.toctree-l1 a, .toctree-l2 a, .toctree-l3 a');
        
        navLinks.forEach(link => {
            const linkHref = link.getAttribute('href');
            
            // If this link points to the current page
            if (linkHref && page.endsWith(linkHref)) {
                // Remove old indicators
                const oldIndicators = link.parentNode.querySelectorAll('.reading-indicator');
                oldIndicators.forEach(ind => ind.remove());
                
                // Add progress indicator
                if (percentage > 10) {
                    const indicator = document.createElement('span');
                    indicator.className = 'reading-indicator';
                    indicator.style.display = 'inline-block';
                    indicator.style.width = '8px';
                    indicator.style.height = '8px';
                    indicator.style.borderRadius = '50%';
                    indicator.style.marginLeft = '5px';
                    
                    // Color based on progress
                    if (percentage < 30) {
                        indicator.style.backgroundColor = '#e74c3c'; // Red
                    } else if (percentage < 80) {
                        indicator.style.backgroundColor = '#f39c12'; // Yellow
                    } else {
                        indicator.style.backgroundColor = '#2ecc71'; // Green
                    }
                    
                    // Add tooltip
                    indicator.title = 'Reading progress: ' + Math.round(percentage) + '%';
                    
                    link.parentNode.appendChild(indicator);
                }
            }
        });
    }
    
    // Load saved progress when the page loads
    function loadSavedProgress() {
        if (typeof localStorage !== 'undefined') {
            try {
                const currentPage = window.location.pathname;
                const savedProgress = localStorage.getItem('readingProgress-' + currentPage);
                
                if (savedProgress) {
                    // If we saved a position, scroll there
                    const scrollHeight = document.body.scrollHeight - window.innerHeight;
                    const scrollPosition = (parseFloat(savedProgress) / 100) * scrollHeight;
                    
                    // Small delay to ensure content is fully loaded
                    setTimeout(() => {
                        window.scrollTo({
                            top: scrollPosition,
                            behavior: 'auto'
                        });
                        
                        // Update the progress bar
                        updateProgress();
                    }, 300);
                }
            } catch (e) {
                console.warn('Unable to load reading progress: ', e);
            }
        }
    }
    
    // Set up events
    window.addEventListener('scroll', updateProgress);
    window.addEventListener('resize', updateProgress);
    
    // Initialize
    updateProgress();
    loadSavedProgress();
}); 