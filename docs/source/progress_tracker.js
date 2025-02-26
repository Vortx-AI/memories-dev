/**
 * Progress Tracker for Memories-Dev Documentation
 * 
 * This script adds a reading progress indicator to documentation pages:
 * 1. Shows a progress bar at the top of the page
 * 2. Displays percentage of page read
 * 3. Estimates reading time
 * 4. Tracks and saves reading history
 */
document.addEventListener('DOMContentLoaded', function() {
    // Only add progress tracker to content pages (not home or search)
    if (document.querySelector('.wy-nav-content .section')) {
        // Create progress tracker elements
        createProgressElements();
        
        // Initialize reading time estimate
        initReadingTimeEstimate();
        
        // Update progress on scroll
        updateProgressOnScroll();
        
        // Save reading history
        trackReadingHistory();
    }
});

/**
 * Create progress tracker UI elements
 */
function createProgressElements() {
    // Create progress bar container
    const progressContainer = document.createElement('div');
    progressContainer.className = 'progress-tracker';
    progressContainer.style.position = 'sticky';
    progressContainer.style.top = '0';
    progressContainer.style.width = '100%';
    progressContainer.style.height = '4px';
    progressContainer.style.backgroundColor = 'rgba(0, 0, 0, 0.05)';
    progressContainer.style.zIndex = '1000';
    
    // Create progress bar
    const progressBar = document.createElement('div');
    progressBar.className = 'progress-bar';
    progressBar.style.height = '100%';
    progressBar.style.width = '0';
    progressBar.style.backgroundColor = '#3b82f6';
    progressBar.style.transition = 'width 0.2s ease-out';
    progressContainer.appendChild(progressBar);
    
    // Create progress stats container
    const statsContainer = document.createElement('div');
    statsContainer.className = 'progress-stats';
    statsContainer.style.position = 'fixed';
    statsContainer.style.bottom = '20px';
    statsContainer.style.right = '20px';
    statsContainer.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
    statsContainer.style.padding = '8px 12px';
    statsContainer.style.borderRadius = '4px';
    statsContainer.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.1)';
    statsContainer.style.fontSize = '13px';
    statsContainer.style.color = '#333';
    statsContainer.style.zIndex = '1000';
    statsContainer.style.display = 'flex';
    statsContainer.style.flexDirection = 'column';
    statsContainer.style.gap = '4px';
    statsContainer.style.opacity = '0.8';
    statsContainer.style.transition = 'opacity 0.2s ease';
    
    // Add hover effect
    statsContainer.addEventListener('mouseenter', function() {
        this.style.opacity = '1';
    });
    
    statsContainer.addEventListener('mouseleave', function() {
        this.style.opacity = '0.8';
    });
    
    // Create progress percentage
    const progressPercentage = document.createElement('div');
    progressPercentage.className = 'progress-percentage';
    progressPercentage.textContent = '0% read';
    statsContainer.appendChild(progressPercentage);
    
    // Create reading time
    const readingTime = document.createElement('div');
    readingTime.className = 'reading-time';
    readingTime.textContent = 'Est. reading time: calculating...';
    statsContainer.appendChild(readingTime);
    
    // Add to page
    const content = document.querySelector('.wy-nav-content');
    if (content) {
        content.prepend(progressContainer);
        document.body.appendChild(statsContainer);
    }
}

/**
 * Calculate and display estimated reading time
 */
function initReadingTimeEstimate() {
    // Get main content
    const content = document.querySelector('.wy-nav-content .section');
    if (!content) return;
    
    // Calculate reading time (average reading speed: 200 words per minute)
    const text = content.textContent || content.innerText;
    const wordCount = text.split(/\s+/).length;
    const readingTimeMinutes = Math.max(1, Math.ceil(wordCount / 200));
    
    // Update reading time display
    const readingTimeElement = document.querySelector('.reading-time');
    if (readingTimeElement) {
        readingTimeElement.textContent = `Est. reading time: ${readingTimeMinutes} min`;
    }
}

/**
 * Update progress bar and stats when scrolling
 */
function updateProgressOnScroll() {
    // Use throttling for better performance
    let ticking = false;
    
    window.addEventListener('scroll', function() {
        if (!ticking) {
            window.requestAnimationFrame(function() {
                updateProgress();
                ticking = false;
            });
            ticking = true;
        }
    });
    
    // Initial update
    updateProgress();
    
    // Update progress function
    function updateProgress() {
        // Calculate scroll progress
        const windowHeight = window.innerHeight;
        const documentHeight = document.documentElement.scrollHeight;
        const scrollTop = window.scrollY;
        
        // Adjust for page height minus viewport
        const scrollableHeight = documentHeight - windowHeight;
        const progress = Math.min(100, Math.max(0, (scrollTop / scrollableHeight) * 100));
        
        // Update progress bar
        const progressBar = document.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }
        
        // Update progress percentage
        const progressPercentage = document.querySelector('.progress-percentage');
        if (progressPercentage) {
            progressPercentage.textContent = `${Math.round(progress)}% read`;
        }
    }
}

/**
 * Track and save reading history
 */
function trackReadingHistory() {
    // Get current page info
    const pageUrl = window.location.pathname;
    const pageTitle = document.title;
    
    // Load reading history from localStorage
    let readingHistory = JSON.parse(localStorage.getItem('memories_dev_reading_history') || '[]');
    
    // Check if page is already in history
    const existingEntryIndex = readingHistory.findIndex(entry => entry.url === pageUrl);
    
    if (existingEntryIndex !== -1) {
        // Update existing entry
        readingHistory[existingEntryIndex].lastVisited = new Date().toISOString();
        readingHistory[existingEntryIndex].visitCount += 1;
    } else {
        // Add new entry
        readingHistory.push({
            url: pageUrl,
            title: pageTitle,
            firstVisited: new Date().toISOString(),
            lastVisited: new Date().toISOString(),
            visitCount: 1,
            completed: false
        });
    }
    
    // Limit history size to 100 entries
    if (readingHistory.length > 100) {
        readingHistory = readingHistory.slice(-100);
    }
    
    // Save updated history
    localStorage.setItem('memories_dev_reading_history', JSON.stringify(readingHistory));
    
    // Track completion on page unload
    window.addEventListener('beforeunload', function() {
        const scrollProgress = Math.min(100, Math.max(0, (window.scrollY / 
            (document.documentElement.scrollHeight - window.innerHeight)) * 100));
        
        // Mark as completed if user read at least 80% of the page
        if (scrollProgress >= 80) {
            let currentHistory = JSON.parse(localStorage.getItem('memories_dev_reading_history') || '[]');
            const entryIndex = currentHistory.findIndex(entry => entry.url === pageUrl);
            
            if (entryIndex !== -1) {
                currentHistory[entryIndex].completed = true;
                localStorage.setItem('memories_dev_reading_history', JSON.stringify(currentHistory));
            }
        }
    });
}
