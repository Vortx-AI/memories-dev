/**
 * Enhanced Book Experience - JavaScript functionality
 * For Memory Codex Documentation
 */

document.addEventListener('DOMContentLoaded', function() {
    initEnhancedBookExperience();
});

/**
 * Initialize all enhanced book experience functionality
 */
function initEnhancedBookExperience() {
    initBookProgress();
    initBookmarkSystem();
    initChapterNavigation();
    initReadingProgress();
    initPageTransitions();
    initTableOfContents();
    initContinueReading();
    initConceptHighlights();
    enhanceCodeBlocks();
}

/**
 * Initialize the book progress bar
 */
function initBookProgress() {
    // Create progress element if not exists
    if (!document.querySelector('.book-progress')) {
        const progressBar = document.createElement('div');
        progressBar.className = 'book-progress';
        progressBar.innerHTML = '<div class="book-progress-bar"></div>';
        document.body.appendChild(progressBar);
    }

    // Update progress on scroll
    window.addEventListener('scroll', function() {
        const scrollPosition = window.scrollY;
        const windowHeight = window.innerHeight;
        const documentHeight = document.documentElement.scrollHeight;
        const scrollPercentage = (scrollPosition / (documentHeight - windowHeight)) * 100;
        
        document.querySelector('.book-progress-bar').style.width = scrollPercentage + '%';
    });
}

/**
 * Initialize bookmark system
 */
function initBookmarkSystem() {
    // Create bookmark container if not exists
    if (!document.querySelector('.bookmark-container')) {
        const bookmarkContainer = document.createElement('div');
        bookmarkContainer.className = 'bookmark-container';
        bookmarkContainer.innerHTML = `
            <div class="bookmark-toggle" title="Bookmarks">🔖</div>
            <div class="bookmark-panel">
                <div class="bookmark-header">
                    <h3>Your Bookmarks</h3>
                    <button class="bookmark-close">×</button>
                </div>
                <div class="bookmark-list"></div>
            </div>
        `;
        document.body.appendChild(bookmarkContainer);
    }

    // Toggle bookmark panel
    document.querySelector('.bookmark-toggle').addEventListener('click', function() {
        document.querySelector('.bookmark-panel').classList.toggle('active');
    });

    // Close bookmark panel
    document.querySelector('.bookmark-close').addEventListener('click', function() {
        document.querySelector('.bookmark-panel').classList.remove('active');
    });

    // Add bookmark button to each section
    document.querySelectorAll('.section').forEach(function(section, index) {
        if (!section.querySelector('.bookmark-section-button') && section.id) {
            const bookmarkButton = document.createElement('button');
            bookmarkButton.className = 'bookmark-section-button';
            bookmarkButton.innerHTML = '🔖';
            bookmarkButton.title = 'Bookmark this section';
            bookmarkButton.dataset.sectionId = section.id;
            
            // Insert after heading
            const heading = section.querySelector('h1, h2, h3, h4, h5, h6');
            if (heading) {
                heading.appendChild(bookmarkButton);
            }
            
            // Add click event
            bookmarkButton.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                addBookmark(this.dataset.sectionId, heading.textContent);
            });
        }
    });

    // Load existing bookmarks
    loadBookmarks();
}

/**
 * Add a bookmark
 */
function addBookmark(sectionId, title) {
    // Get existing bookmarks
    let bookmarks = JSON.parse(localStorage.getItem('memoryCodexBookmarks') || '[]');
    
    // Check if already bookmarked
    const exists = bookmarks.find(bookmark => bookmark.id === sectionId);
    if (exists) {
        showNotification('This section is already bookmarked');
        return;
    }
    
    // Add new bookmark
    const newBookmark = {
        id: sectionId,
        title: title.trim(),
        url: window.location.pathname + '#' + sectionId,
        date: new Date().toISOString(),
        page: document.title
    };
    
    bookmarks.push(newBookmark);
    
    // Save bookmarks
    localStorage.setItem('memoryCodexBookmarks', JSON.stringify(bookmarks));
    
    // Update bookmark list
    loadBookmarks();
    
    // Show notification
    showNotification('Bookmark added');
}

/**
 * Load bookmarks from localStorage
 */
function loadBookmarks() {
    const bookmarkList = document.querySelector('.bookmark-list');
    const bookmarks = JSON.parse(localStorage.getItem('memoryCodexBookmarks') || '[]');
    
    if (bookmarks.length === 0) {
        bookmarkList.innerHTML = '<div class="no-bookmarks">No bookmarks yet</div>';
        return;
    }
    
    bookmarkList.innerHTML = '';
    
    // Sort bookmarks by date (newest first)
    bookmarks.sort((a, b) => new Date(b.date) - new Date(a.date));
    
    bookmarks.forEach(function(bookmark) {
        const item = document.createElement('div');
        item.className = 'bookmark-item';
        item.innerHTML = `
            <a href="${bookmark.url}" class="bookmark-link">${bookmark.title}</a>
            <div class="bookmark-date">From: ${bookmark.page}</div>
            <div class="bookmark-controls">
                <button class="bookmark-remove" data-id="${bookmark.id}">Remove</button>
            </div>
        `;
        bookmarkList.appendChild(item);
    });
    
    // Add remove event listeners
    document.querySelectorAll('.bookmark-remove').forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            removeBookmark(this.dataset.id);
        });
    });
}

/**
 * Remove a bookmark
 */
function removeBookmark(id) {
    let bookmarks = JSON.parse(localStorage.getItem('memoryCodexBookmarks') || '[]');
    bookmarks = bookmarks.filter(bookmark => bookmark.id !== id);
    localStorage.setItem('memoryCodexBookmarks', JSON.stringify(bookmarks));
    loadBookmarks();
    showNotification('Bookmark removed');
}

/**
 * Show a notification
 */
function showNotification(message) {
    // Remove existing notification
    const existingNotification = document.querySelector('.book-notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    // Create new notification
    const notification = document.createElement('div');
    notification.className = 'book-notification';
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => notification.classList.add('active'), 10);
    
    // Hide notification after 3 seconds
    setTimeout(() => {
        notification.classList.remove('active');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

/**
 * Initialize enhanced chapter navigation
 */
function initChapterNavigation() {
    const content = document.querySelector('.book-content') || document.querySelector('.rst-content');
    if (!content) return;
    
    // Get prev/next links from footer
    const prevLink = document.querySelector('.rst-footer-buttons .btn-neutral:first-child');
    const nextLink = document.querySelector('.rst-footer-buttons .btn-neutral:last-child');
    
    if (!prevLink && !nextLink) return;
    
    // Create enhanced navigation
    const nav = document.createElement('div');
    nav.className = 'chapter-navigation';
    
    // Previous chapter
    if (prevLink) {
        const prevTitle = prevLink.querySelector('.title') ? 
                        prevLink.querySelector('.title').textContent : 
                        prevLink.textContent.trim();
        
        nav.innerHTML += `
            <div class="prev-chapter">
                <a href="${prevLink.href}" class="nav-link">
                    <div class="nav-direction">Previous Chapter</div>
                    <div class="nav-title">${prevTitle}</div>
                </a>
            </div>
        `;
    } else {
        nav.innerHTML += '<div class="prev-chapter"></div>';
    }
    
    // Next chapter
    if (nextLink) {
        const nextTitle = nextLink.querySelector('.title') ? 
                        nextLink.querySelector('.title').textContent : 
                        nextLink.textContent.trim();
        
        nav.innerHTML += `
            <div class="next-chapter">
                <a href="${nextLink.href}" class="nav-link">
                    <div class="nav-direction">Next Chapter</div>
                    <div class="nav-title">${nextTitle}</div>
                </a>
            </div>
        `;
    } else {
        nav.innerHTML += '<div class="next-chapter"></div>';
    }
    
    // Append navigation
    content.appendChild(nav);
}

/**
 * Initialize reading progress tracker
 */
function initReadingProgress() {
    // Get visited pages from localStorage
    const visitedPages = JSON.parse(localStorage.getItem('memoryCodexVisited') || '[]');
    
    // Add current page to visited pages if not already included
    const currentPath = window.location.pathname;
    if (!visitedPages.includes(currentPath) && !currentPath.includes('index.html')) {
        visitedPages.push(currentPath);
        localStorage.setItem('memoryCodexVisited', JSON.stringify(visitedPages));
    }
    
    // Get total number of pages from meta tag or estimate
    const totalPages = 30; // Default estimate
    
    // Update progress display
    const progressElements = document.querySelectorAll('.pages-read');
    progressElements.forEach(function(element) {
        element.textContent = `${visitedPages.length} chapters explored`;
    });
    
    // Update progress bar
    const progressBars = document.querySelectorAll('.progress');
    const percentage = Math.min(100, Math.round((visitedPages.length / totalPages) * 100));
    progressBars.forEach(function(bar) {
        bar.style.width = percentage + '%';
    });
}

/**
 * Initialize page transitions
 */
function initPageTransitions() {
    document.body.classList.add('page-transition');
}

/**
 * Initialize table of contents interactions
 */
function initTableOfContents() {
    // Check if we're on the TOC page
    const isTocPage = window.location.pathname.includes('table_of_contents');
    
    if (isTocPage) {
        // Add TOC container class
        const content = document.querySelector('.rst-content .section');
        if (content) {
            content.classList.add('toc-container');
            
            // Add section classes
            content.querySelectorAll('h2').forEach(function(heading) {
                const section = heading.parentElement;
                section.classList.add('toc-section');
                
                // Find all list items until next h2
                let currentElement = heading.nextElementSibling;
                while (currentElement && currentElement.tagName !== 'H2') {
                    if (currentElement.tagName === 'UL') {
                        const items = currentElement.querySelectorAll('li');
                        items.forEach(function(item) {
                            item.classList.add('toc-item');
                            
                            // Format links
                            const link = item.querySelector('a');
                            if (link) {
                                const text = link.textContent;
                                link.innerHTML = text;
                            }
                            
                            // Format sublists
                            const sublist = item.querySelector('ul');
                            if (sublist) {
                                sublist.classList.add('toc-item-content');
                            }
                        });
                    }
                    currentElement = currentElement.nextElementSibling;
                }
            });
        }
    }
}

/**
 * Initialize "Continue Reading" functionality
 */
function initContinueReading() {
    const continueButton = document.getElementById('continue-reading');
    if (!continueButton) return;
    
    // Get last visited page from localStorage
    const visitedPages = JSON.parse(localStorage.getItem('memoryCodexVisited') || '[]');
    
    if (visitedPages.length > 0) {
        // Get the last visited page
        const lastPage = visitedPages[visitedPages.length - 1];
        continueButton.href = lastPage;
    } else {
        // If no visited pages, link to first chapter
        continueButton.href = 'introduction/index.html';
    }
}

/**
 * Initialize concept highlights
 */
function initConceptHighlights() {
    // Find and enhance admonition blocks
    document.querySelectorAll('.admonition.note').forEach(function(note) {
        const title = note.querySelector('.admonition-title');
        if (title && title.textContent.includes('Concept:')) {
            note.classList.add('concept-highlight');
        }
    });
}

/**
 * Enhance code blocks with syntax highlighting and copy button
 */
function enhanceCodeBlocks() {
    document.querySelectorAll('pre').forEach(function(pre) {
        // Skip if already processed
        if (pre.querySelector('.copy-code-button')) return;
        
        // Add copy button
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-code-button';
        copyButton.innerHTML = 'Copy';
        copyButton.title = 'Copy to clipboard';
        
        // Determine language from class
        let language = 'text';
        pre.classList.forEach(function(className) {
            if (className.startsWith('language-')) {
                language = className.replace('language-', '');
            }
        });
        
        // Add language indicator
        const languageIndicator = document.createElement('div');
        languageIndicator.className = 'code-language';
        languageIndicator.textContent = language;
        
        // Add elements to pre
        pre.appendChild(copyButton);
        pre.appendChild(languageIndicator);
        
        // Add copy functionality
        copyButton.addEventListener('click', function() {
            const code = pre.querySelector('code') ? 
                        pre.querySelector('code').textContent : 
                        pre.textContent;
            
            navigator.clipboard.writeText(code).then(function() {
                // Change button text temporarily
                copyButton.innerHTML = 'Copied!';
                setTimeout(function() {
                    copyButton.innerHTML = 'Copy';
                }, 2000);
            }).catch(function(err) {
                console.error('Could not copy text: ', err);
            });
        });
    });
} 