// Guided Tour for memories-dev documentation
document.addEventListener('DOMContentLoaded', function() {
    // Initialize guided tour
    initializeGuidedTour();
});

/**
 * Initialize the guided tour component
 */
function initializeGuidedTour() {
    // Add tour button to the navigation
    addTourButton();
    
    // Add styles for guided tour
    addGuidedTourStyles();
    
    // Check if tour should start automatically
    checkAutoStartTour();
}

/**
 * Add tour button to the navigation
 */
function addTourButton() {
    // Create tour button
    const tourButton = document.createElement('button');
    tourButton.className = 'guided-tour-button';
    tourButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16zm.93-9.412-1 4.705c-.07.34.029.533.304.533.194 0 .487-.07.686-.246l-.088.416c-.287.346-.92.598-1.465.598-.703 0-1.002-.422-.808-1.319l.738-3.468c.064-.293.006-.399-.287-.47l-.451-.081.082-.381 2.29-.287zM8 5.5a1 1 0 1 1 0-2 1 1 0 0 1 0 2z"/></svg> Take a Tour';
    tourButton.setAttribute('aria-label', 'Start guided tour');
    
    // Add click event
    tourButton.addEventListener('click', function() {
        startGuidedTour();
    });
    
    // Add to navigation
    const navContent = document.querySelector('.wy-side-nav-search');
    if (navContent) {
        navContent.appendChild(tourButton);
    } else {
        // Fallback to body if nav not found
        document.body.insertBefore(tourButton, document.body.firstChild);
    }
}

/**
 * Check if tour should start automatically
 */
function checkAutoStartTour() {
    // Check URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const startTour = urlParams.get('tour');
    
    // Start tour if parameter is present
    if (startTour === 'true' || startTour === '1') {
        // Delay start to ensure page is fully loaded
        setTimeout(function() {
            startGuidedTour();
        }, 1000);
    }
    
    // Check if first-time visitor
    const isFirstVisit = !localStorage.getItem('tour_completed');
    if (isFirstVisit && window.location.pathname.endsWith('/index.html')) {
        // Show tour prompt for first-time visitors on index page
        showTourPrompt();
    }
}

/**
 * Show tour prompt for first-time visitors
 */
function showTourPrompt() {
    // Create prompt container
    const promptContainer = document.createElement('div');
    promptContainer.className = 'tour-prompt';
    
    // Create prompt content
    promptContainer.innerHTML = `
        <div class="tour-prompt-content">
            <h3>Welcome to memories-dev Documentation!</h3>
            <p>Would you like a quick tour to help you navigate the documentation?</p>
            <div class="tour-prompt-buttons">
                <button class="tour-prompt-start">Yes, show me around</button>
                <button class="tour-prompt-skip">No, thanks</button>
            </div>
        </div>
    `;
    
    // Add event listeners
    promptContainer.querySelector('.tour-prompt-start').addEventListener('click', function() {
        promptContainer.remove();
        startGuidedTour();
    });
    
    promptContainer.querySelector('.tour-prompt-skip').addEventListener('click', function() {
        promptContainer.remove();
        localStorage.setItem('tour_completed', 'true');
    });
    
    // Add to body
    document.body.appendChild(promptContainer);
    
    // Auto-hide after 15 seconds if no interaction
    setTimeout(function() {
        if (document.body.contains(promptContainer)) {
            promptContainer.remove();
        }
    }, 15000);
}

/**
 * Start the guided tour
 */
function startGuidedTour() {
    // Define tour steps based on current page
    const tourSteps = defineTourSteps();
    
    // Create tour overlay
    const tourOverlay = document.createElement('div');
    tourOverlay.className = 'tour-overlay';
    document.body.appendChild(tourOverlay);
    
    // Create tour container
    const tourContainer = document.createElement('div');
    tourContainer.className = 'tour-container';
    document.body.appendChild(tourContainer);
    
    // Initialize tour state
    let currentStep = 0;
    
    // Function to show current step
    function showStep(stepIndex) {
        // Get step data
        const step = tourSteps[stepIndex];
        
        // Find target element
        const targetElement = document.querySelector(step.target);
        if (!targetElement) {
            console.error(`Tour target not found: ${step.target}`);
            nextStep();
            return;
        }
        
        // Position tour container
        positionTourStep(tourContainer, targetElement, step.position);
        
        // Update content
        tourContainer.innerHTML = `
            <div class="tour-header">
                <span class="tour-step">${stepIndex + 1}/${tourSteps.length}</span>
                <button class="tour-close" aria-label="Close tour">&times;</button>
            </div>
            <div class="tour-content">
                <h3>${step.title}</h3>
                <p>${step.content}</p>
            </div>
            <div class="tour-footer">
                ${stepIndex > 0 ? '<button class="tour-prev">Previous</button>' : ''}
                ${stepIndex < tourSteps.length - 1 ? 
                    '<button class="tour-next">Next</button>' : 
                    '<button class="tour-finish">Finish Tour</button>'}
            </div>
        `;
        
        // Highlight target element
        highlightElement(targetElement);
        
        // Add event listeners
        tourContainer.querySelector('.tour-close').addEventListener('click', endTour);
        
        const prevButton = tourContainer.querySelector('.tour-prev');
        if (prevButton) {
            prevButton.addEventListener('click', prevStep);
        }
        
        const nextButton = tourContainer.querySelector('.tour-next');
        if (nextButton) {
            nextButton.addEventListener('click', nextStep);
        }
        
        const finishButton = tourContainer.querySelector('.tour-finish');
        if (finishButton) {
            finishButton.addEventListener('click', endTour);
        }
    }
    
    // Function to highlight target element
    function highlightElement(element) {
        // Reset previous highlights
        document.querySelectorAll('.tour-highlight').forEach(el => {
            el.classList.remove('tour-highlight');
        });
        
        // Add highlight class
        element.classList.add('tour-highlight');
        
        // Scroll element into view if needed
        const rect = element.getBoundingClientRect();
        const isInViewport = (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= window.innerHeight &&
            rect.right <= window.innerWidth
        );
        
        if (!isInViewport) {
            element.scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });
        }
    }
    
    // Function to position tour step
    function positionTourStep(container, target, position = 'bottom') {
        const targetRect = target.getBoundingClientRect();
        const containerWidth = 300; // Fixed width for tour container
        
        // Reset container styles
        container.style.top = '';
        container.style.right = '';
        container.style.bottom = '';
        container.style.left = '';
        
        // Position based on specified position
        switch (position) {
            case 'top':
                container.style.bottom = `${window.innerHeight - targetRect.top + 10}px`;
                container.style.left = `${targetRect.left + (targetRect.width / 2) - (containerWidth / 2)}px`;
                break;
            case 'right':
                container.style.top = `${targetRect.top + (targetRect.height / 2) - 100}px`;
                container.style.left = `${targetRect.right + 10}px`;
                break;
            case 'bottom':
                container.style.top = `${targetRect.bottom + 10}px`;
                container.style.left = `${targetRect.left + (targetRect.width / 2) - (containerWidth / 2)}px`;
                break;
            case 'left':
                container.style.top = `${targetRect.top + (targetRect.height / 2) - 100}px`;
                container.style.right = `${window.innerWidth - targetRect.left + 10}px`;
                break;
        }
        
        // Ensure container is within viewport
        const containerRect = container.getBoundingClientRect();
        
        if (containerRect.left < 10) {
            container.style.left = '10px';
        } else if (containerRect.right > window.innerWidth - 10) {
            container.style.left = `${window.innerWidth - containerWidth - 10}px`;
        }
        
        if (containerRect.top < 10) {
            container.style.top = '10px';
        } else if (containerRect.bottom > window.innerHeight - 10) {
            container.style.top = `${window.innerHeight - containerRect.height - 10}px`;
        }
    }
    
    // Function to go to next step
    function nextStep() {
        currentStep++;
        if (currentStep < tourSteps.length) {
            showStep(currentStep);
        } else {
            endTour();
        }
    }
    
    // Function to go to previous step
    function prevStep() {
        currentStep--;
        if (currentStep >= 0) {
            showStep(currentStep);
        }
    }
    
    // Function to end tour
    function endTour() {
        // Remove tour elements
        tourContainer.remove();
        tourOverlay.remove();
        
        // Remove highlights
        document.querySelectorAll('.tour-highlight').forEach(el => {
            el.classList.remove('tour-highlight');
        });
        
        // Mark tour as completed
        localStorage.setItem('tour_completed', 'true');
    }
    
    // Start with first step
    showStep(currentStep);
    
    // Add keyboard navigation
    document.addEventListener('keydown', function tourKeyHandler(e) {
        if (e.key === 'Escape') {
            endTour();
            document.removeEventListener('keydown', tourKeyHandler);
        } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
            nextStep();
        } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
            prevStep();
        }
    });
}

/**
 * Define tour steps based on current page
 */
function defineTourSteps() {
    // Default steps for all pages
    const defaultSteps = [
        {
            target: '.wy-side-nav-search',
            position: 'right',
            title: 'Documentation Search',
            content: 'Use this search box to find specific topics or keywords throughout the documentation.'
        },
        {
            target: '.wy-menu-vertical',
            position: 'right',
            title: 'Navigation Menu',
            content: 'Browse through different sections of the documentation using this navigation menu.'
        },
        {
            target: '.rst-content',
            position: 'left',
            title: 'Content Area',
            content: 'This is where the main documentation content is displayed.'
        },
        {
            target: '.theme-toggle-container',
            position: 'right',
            title: 'Theme Toggle',
            content: 'Switch between light and dark themes based on your preference.'
        }
    ];
    
    // Check if we're on the index page
    if (window.location.pathname.endsWith('/index.html') || window.location.pathname.endsWith('/')) {
        return [
            {
                target: '.hero-banner',
                position: 'bottom',
                title: 'Welcome to memories-dev',
                content: 'This is the documentation for the memories-dev framework, Earth\'s Unified Memory System for Artificial General Intelligence.'
            },
            {
                target: '.hero-buttons',
                position: 'bottom',
                title: 'Quick Access',
                content: 'Use these buttons to quickly get started or visit the GitHub repository.'
            },
            {
                target: '.comparison-table',
                position: 'top',
                title: 'Key Advantages',
                content: 'This comparison table highlights the advantages of memories-dev over traditional AI approaches.'
            },
            ...defaultSteps,
            {
                target: '.wy-nav-side',
                position: 'right',
                title: 'Documentation Structure',
                content: 'The documentation is organized into sections: Getting Started, User Guide, Core Concepts, Earth Memory, Algorithms, API Reference, Examples, and Metrics.'
            }
        ];
    }
    
    // Check if we're on an API reference page
    if (window.location.pathname.includes('/api_reference/')) {
        return [
            ...defaultSteps,
            {
                target: '.api-explorer',
                position: 'top',
                title: 'Interactive API Explorer',
                content: 'Try out API endpoints directly in the documentation using this interactive explorer.'
            },
            {
                target: '.highlight-python',
                position: 'top',
                title: 'Code Examples',
                content: 'Code examples show you how to use the API in your applications.'
            }
        ];
    }
    
    // Check if we're on an examples page
    if (window.location.pathname.includes('/examples/')) {
        return [
            ...defaultSteps,
            {
                target: '.code-playground',
                position: 'top',
                title: 'Interactive Code Playground',
                content: 'Try out code examples directly in the documentation using this interactive playground.'
            }
        ];
    }
    
    // Default to basic steps for other pages
    return defaultSteps;
}

/**
 * Add styles for guided tour
 */
function addGuidedTourStyles() {
    const style = document.createElement('style');
    style.textContent = `
        /* Tour Button */
        .guided-tour-button {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            margin-top: 1rem;
            padding: 8px 16px;
            background-color: var(--accent-color, #4285f4);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 500;
            transition: background-color 0.2s, transform 0.2s;
            width: 100%;
        }
        
        .guided-tour-button:hover {
            background-color: var(--accent-dark, #3367d6);
            transform: translateY(-2px);
        }
        
        .guided-tour-button svg {
            flex-shrink: 0;
        }
        
        /* Tour Prompt */
        .tour-prompt {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
            max-width: 350px;
            background-color: var(--primary-light, #f8f9fa);
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            border-left: 4px solid var(--accent-color, #4285f4);
            animation: slideIn 0.3s ease-out;
        }
        
        @keyframes slideIn {
            from {
                transform: translateY(100px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
        
        .tour-prompt-content {
            padding: 16px;
        }
        
        .tour-prompt-content h3 {
            margin-top: 0;
            margin-bottom: 8px;
            font-size: 18px;
            color: var(--text-color, #202124);
        }
        
        .tour-prompt-content p {
            margin-bottom: 16px;
            color: var(--text-muted, #5f6368);
        }
        
        .tour-prompt-buttons {
            display: flex;
            gap: 8px;
        }
        
        .tour-prompt-start {
            padding: 8px 16px;
            background-color: var(--accent-color, #4285f4);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 500;
        }
        
        .tour-prompt-start:hover {
            background-color: var(--accent-dark, #3367d6);
        }
        
        .tour-prompt-skip {
            padding: 8px 16px;
            background-color: transparent;
            color: var(--text-color, #202124);
            border: 1px solid var(--border-color, #dadce0);
            border-radius: 4px;
            cursor: pointer;
        }
        
        .tour-prompt-skip:hover {
            background-color: var(--primary-dark, #e9ecef);
        }
        
        /* Tour Overlay */
        .tour-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 998;
            pointer-events: none;
        }
        
        /* Tour Container */
        .tour-container {
            position: fixed;
            width: 300px;
            background-color: var(--primary-light, #f8f9fa);
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 999;
            overflow: hidden;
        }
        
        .tour-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            background-color: var(--accent-color, #4285f4);
            color: white;
        }
        
        .tour-step {
            font-size: 14px;
            font-weight: 500;
        }
        
        .tour-close {
            background: none;
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
            padding: 0;
            line-height: 1;
        }
        
        .tour-content {
            padding: 16px;
        }
        
        .tour-content h3 {
            margin-top: 0;
            margin-bottom: 8px;
            font-size: 18px;
            color: var(--text-color, #202124);
        }
        
        .tour-content p {
            margin-bottom: 0;
            color: var(--text-muted, #5f6368);
            font-size: 14px;
            line-height: 1.5;
        }
        
        .tour-footer {
            display: flex;
            justify-content: flex-end;
            gap: 8px;
            padding: 12px 16px;
            border-top: 1px solid var(--border-color, #dadce0);
        }
        
        .tour-prev, .tour-next, .tour-finish {
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 500;
            font-size: 14px;
        }
        
        .tour-prev {
            background-color: transparent;
            color: var(--text-color, #202124);
            border: 1px solid var(--border-color, #dadce0);
        }
        
        .tour-prev:hover {
            background-color: var(--primary-dark, #e9ecef);
        }
        
        .tour-next, .tour-finish {
            background-color: var(--accent-color, #4285f4);
            color: white;
            border: none;
        }
        
        .tour-next:hover, .tour-finish:hover {
            background-color: var(--accent-dark, #3367d6);
        }
        
        /* Highlight */
        .tour-highlight {
            position: relative;
            z-index: 1000;
            box-shadow: 0 0 0 4px var(--accent-color, #4285f4);
            border-radius: 4px;
        }
        
        /* Responsive styles */
        @media (max-width: 768px) {
            .tour-container {
                width: calc(100% - 40px);
                max-width: 300px;
            }
            
            .tour-prompt {
                left: 20px;
                right: 20px;
                max-width: none;
            }
        }
    `;
    
    document.head.appendChild(style);
} 