/**
 * book_experience.js
 * Enhances the documentation with book-like reading experience features
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if book experience is enabled
    if (window.DOCUMENTATION_OPTIONS && window.DOCUMENTATION_OPTIONS.ENABLE_BOOK_EXPERIENCE) {
        // Initialize all enhancements
        initializeBookCover();
        initializeProgressTracker();
        addChapterNavigationControls();
        enhanceCodeSamples();
        addPageTurningEffect();
        addBookmarkSystem();
        addReadingTimeEstimates();
    }
});

/**
 * Initializes the interactive 3D book cover
 */
function initializeBookCover() {
    const bookCover = document.querySelector('.book');
    if (!bookCover) return;

    // Add 3D rotation effect
    bookCover.addEventListener('mousemove', function(e) {
        const xAxis = (window.innerWidth / 2 - e.pageX) / 25;
        const yAxis = (window.innerHeight / 2 - e.pageY) / 25;
        bookCover.style.transform = `rotateY(${xAxis}deg) rotateX(${yAxis}deg)`;
    });

    // Reset position when mouse leaves
    bookCover.addEventListener('mouseleave', function() {
        bookCover.style.transform = 'rotateY(-30deg) rotateX(0deg)';
        setTimeout(() => {
            bookCover.style.transition = 'transform 0.5s ease';
        }, 100);
    });

    // Add transition only after initial load
    setTimeout(() => {
        bookCover.style.transition = 'transform 0.5s ease';
    }, 100);

    // "Open" book on click
    bookCover.addEventListener('click', function() {
        bookCover.classList.toggle('open');
        
        // If the book is opened, scroll to content after animation
        if (bookCover.classList.contains('open')) {
            setTimeout(() => {
                const firstHeading = document.querySelector('.rst-content h1');
                if (firstHeading) {
                    firstHeading.scrollIntoView({ behavior: 'smooth' });
                }
            }, 600);
        }
    });
}

/**
 * Tracks reading progress through the documentation
 */
function initializeProgressTracker() {
    const progressContainer = document.getElementById('reading-progress-container');
    if (!progressContainer) return;

    const progressBar = document.querySelector('.progress');
    const pagesRead = document.querySelector('.pages-read');
    
    // Calculate current progress
    const totalSections = document.querySelectorAll('.section').length || 30; // Default to 30 if can't count
    const visitedPages = getVisitedPages();
    const progressPercentage = Math.min(100, (visitedPages.length / totalSections) * 100);
    
    // Update the UI
    if (progressBar) {
        progressBar.style.width = `${progressPercentage}%`;
    }
    
    if (pagesRead) {
        pagesRead.textContent = `${visitedPages.length} sections read`;
    }
    
    // Mark current page as read
    const currentPath = window.location.pathname;
    savePageVisit(currentPath);
}

/**
 * Retrieves array of visited pages from localStorage
 */
function getVisitedPages() {
    try {
        const visited = localStorage.getItem('memoriesDevVisitedPages');
        return visited ? JSON.parse(visited) : [];
    } catch (e) {
        console.error('Error accessing localStorage:', e);
        return [];
    }
}

/**
 * Saves page visit to localStorage
 */
function savePageVisit(pagePath) {
    try {
        const visited = getVisitedPages();
        if (!visited.includes(pagePath)) {
            visited.push(pagePath);
            localStorage.setItem('memoriesDevVisitedPages', JSON.stringify(visited));
        }
    } catch (e) {
        console.error('Error saving to localStorage:', e);
    }
}

/**
 * Adds previous/next chapter navigation controls
 */
function addChapterNavigationControls() {
    const content = document.querySelector('.rst-content');
    if (!content) return;
    
    // Get next/prev links from the built-in sphinx navigation
    const nextLink = document.querySelector('a.next');
    const prevLink = document.querySelector('a.prev');
    
    if (!nextLink && !prevLink) return; // Don't add nav if no links
    
    // Create custom navigation container
    const navContainer = document.createElement('div');
    navContainer.className = 'book-navigation';
    
    // Add previous chapter button if available
    if (prevLink) {
        const prevButton = document.createElement('div');
        prevButton.className = 'book-nav-button prev-chapter';
        prevButton.innerHTML = `<span class="nav-arrow">←</span> <span class="nav-text">Previous Chapter:<br>${prevLink.title}</span>`;
        prevButton.addEventListener('click', function() {
            window.location.href = prevLink.href;
        });
        navContainer.appendChild(prevButton);
    }
    
    // Add next chapter button if available
    if (nextLink) {
        const nextButton = document.createElement('div');
        nextButton.className = 'book-nav-button next-chapter';
        nextButton.innerHTML = `<span class="nav-text">Next Chapter:<br>${nextLink.title}</span> <span class="nav-arrow">→</span>`;
        nextButton.addEventListener('click', function() {
            window.location.href = nextLink.href;
        });
        navContainer.appendChild(nextButton);
    }
    
    // Add to the bottom of the content
    content.appendChild(navContainer);
}

/**
 * Enhances code samples with copy button and syntax highlighting
 */
function enhanceCodeSamples() {
    const codeBlocks = document.querySelectorAll('div[class^="highlight-"]');
    
    codeBlocks.forEach(block => {
        // Add copy button
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-button';
        copyButton.textContent = 'Copy';
        copyButton.addEventListener('click', function() {
            const code = block.querySelector('pre').textContent;
            navigator.clipboard.writeText(code).then(() => {
                copyButton.textContent = 'Copied!';
                setTimeout(() => {
                    copyButton.textContent = 'Copy';
                }, 2000);
            });
        });
        
        // Add button to code block
        block.style.position = 'relative';
        block.appendChild(copyButton);
    });
}

/**
 * Adds subtle page turning effect when navigating
 */
function addPageTurningEffect() {
    // Store current scroll position
    document.addEventListener('click', function(e) {
        const target = e.target.closest('a');
        if (target && target.href && target.href.startsWith(window.location.origin)) {
            sessionStorage.setItem('scrollPosition', window.scrollY);
        }
    });
    
    // Check if we need to animate
    if (performance.navigation.type === 1 || performance.navigation.type === 0) {
        const content = document.querySelector('.document');
        if (content) {
            content.style.opacity = '0';
            content.style.transform = 'translateX(20px)';
            
            // Animate in
            setTimeout(() => {
                content.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
                content.style.opacity = '1';
                content.style.transform = 'translateX(0)';
            }, 10);
        }
    }
}

/**
 * Adds a bookmark system to save reading positions
 */
function addBookmarkSystem() {
    const articleContent = document.querySelector('article.content');
    if (!articleContent) return;
    
    // Create bookmark button
    const bookmarkButton = document.createElement('button');
    bookmarkButton.className = 'bookmark-button';
    bookmarkButton.innerHTML = '<span class="bookmark-icon">🔖</span> Bookmark';
    
    // Handle bookmark functionality
    bookmarkButton.addEventListener('click', function() {
        const currentPath = window.location.pathname;
        const scrollPosition = window.scrollY;
        const pageTitle = document.title;
        
        // Save bookmark
        saveBookmark(currentPath, scrollPosition, pageTitle);
        
        // Update button appearance
        bookmarkButton.classList.add('bookmarked');
        bookmarkButton.innerHTML = '<span class="bookmark-icon">🔖</span> Bookmarked';
        
        // Reset after delay
        setTimeout(() => {
            bookmarkButton.classList.remove('bookmarked');
            bookmarkButton.innerHTML = '<span class="bookmark-icon">🔖</span> Bookmark';
        }, 2000);
    });
    
    // Add to document
    const bookmarkContainer = document.createElement('div');
    bookmarkContainer.className = 'bookmark-container';
    bookmarkContainer.appendChild(bookmarkButton);
    articleContent.insertBefore(bookmarkContainer, articleContent.firstChild);
    
    // Check if there's a bookmark for this page and show indicator
    const currentPath = window.location.pathname;
    const bookmark = getBookmark(currentPath);
    if (bookmark) {
        const indicator = document.createElement('div');
        indicator.className = 'resume-reading';
        indicator.textContent = 'Resume reading';
        indicator.addEventListener('click', function() {
            window.scrollTo({
                top: bookmark.position,
                behavior: 'smooth'
            });
            indicator.style.display = 'none';
        });
        bookmarkContainer.appendChild(indicator);
    }
}

/**
 * Saves a bookmark to localStorage
 */
function saveBookmark(path, position, title) {
    const bookmarks = getBookmarks();
    bookmarks[path] = {
        position: position,
        title: title,
        timestamp: new Date().toISOString()
    };
    localStorage.setItem('memoriesDevBookmarks', JSON.stringify(bookmarks));
}

/**
 * Gets a specific bookmark by path
 */
function getBookmark(path) {
    const bookmarks = getBookmarks();
    return bookmarks[path];
}

/**
 * Gets all bookmarks from localStorage
 */
function getBookmarks() {
    const bookmarks = localStorage.getItem('memoriesDevBookmarks');
    return bookmarks ? JSON.parse(bookmarks) : {};
}

/**
 * Adds reading time estimates to documentation pages
 */
function addReadingTimeEstimates() {
    const content = document.querySelector('.document');
    if (!content) return;
    
    // Calculate reading time based on content
    const text = content.textContent;
    const wordCount = text.split(/\s+/).length;
    const readingTimeMinutes = Math.max(1, Math.round(wordCount / 200)); // Assuming 200 words per minute
    
    // Create reading time indicator
    const readingTime = document.createElement('div');
    readingTime.className = 'reading-time';
    readingTime.innerHTML = `<span class="reading-time-icon">⏱️</span> ${readingTimeMinutes} min read`;
    
    // Add to document
    const contentHeader = document.querySelector('.page-header, h1');
    if (contentHeader) {
        contentHeader.insertAdjacentElement('afterend', readingTime);
    }
} 