// Advanced Search Enhancer for memories-dev documentation
document.addEventListener('DOMContentLoaded', function() {
    // Enhance search input
    enhanceSearchInput();
    
    // Add keyboard shortcuts for search
    addSearchKeyboardShortcuts();
    
    // Add search filters
    addSearchFilters();
    
    // Improve search results display
    improveSearchResults();
});

/**
 * Enhance the search input with autocomplete and suggestions
 */
function enhanceSearchInput() {
    const searchInput = document.querySelector('input[name="q"]');
    if (!searchInput) return;
    
    // Add placeholder text
    searchInput.setAttribute('placeholder', 'Search documentation...');
    
    // Add autocomplete attribute
    searchInput.setAttribute('autocomplete', 'off');
    
    // Add aria attributes for accessibility
    searchInput.setAttribute('aria-label', 'Search documentation');
    
    // Create search suggestions container
    const suggestionsContainer = document.createElement('div');
    suggestionsContainer.className = 'search-suggestions';
    suggestionsContainer.style.display = 'none';
    
    // Insert suggestions container after search input
    searchInput.parentNode.style.position = 'relative';
    searchInput.parentNode.appendChild(suggestionsContainer);
    
    // Common search terms (these would ideally be generated from content)
    const commonSearchTerms = [
        'memory system', 'spatial analysis', 'temporal analysis', 
        'data sources', 'API reference', 'configuration', 
        'installation', 'quickstart', 'examples',
        'memory store', 'data utils', 'models'
    ];
    
    // Add input event listener for suggestions
    searchInput.addEventListener('input', function() {
        const query = this.value.trim().toLowerCase();
        
        // Clear suggestions
        suggestionsContainer.innerHTML = '';
        
        // Hide suggestions if query is empty
        if (query.length < 2) {
            suggestionsContainer.style.display = 'none';
            return;
        }
        
        // Filter common search terms
        const matchingTerms = commonSearchTerms.filter(term => 
            term.toLowerCase().includes(query)
        );
        
        // Add matching terms to suggestions
        if (matchingTerms.length > 0) {
            matchingTerms.slice(0, 5).forEach(term => {
                const suggestion = document.createElement('div');
                suggestion.className = 'search-suggestion';
                suggestion.textContent = term;
                
                // Add click event to fill search input
                suggestion.addEventListener('click', function() {
                    searchInput.value = term;
                    suggestionsContainer.style.display = 'none';
                    
                    // Focus search input and trigger search
                    searchInput.focus();
                    
                    // Submit the search form
                    const searchForm = searchInput.closest('form');
                    if (searchForm) {
                        searchForm.submit();
                    }
                });
                
                suggestionsContainer.appendChild(suggestion);
            });
            
            // Show suggestions
            suggestionsContainer.style.display = 'block';
        } else {
            suggestionsContainer.style.display = 'none';
        }
    });
    
    // Hide suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !suggestionsContainer.contains(e.target)) {
            suggestionsContainer.style.display = 'none';
        }
    });
    
    // Add styles for search suggestions
    const style = document.createElement('style');
    style.textContent = `
        .search-suggestions {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background-color: var(--primary-light);
            border: 1px solid var(--border-color);
            border-top: none;
            border-radius: 0 0 4px 4px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            z-index: 1000;
            max-height: 200px;
            overflow-y: auto;
        }
        
        .search-suggestion {
            padding: 8px 12px;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        
        .search-suggestion:hover {
            background-color: var(--accent-color);
            color: white;
        }
        
        /* Improve search input styling */
        .wy-side-nav-search input[type="text"] {
            border-radius: 4px;
            padding: 8px 12px;
            font-size: 14px;
            transition: all 0.3s;
            width: 100%;
        }
        
        .wy-side-nav-search input[type="text"]:focus {
            box-shadow: 0 0 0 2px var(--accent-color);
            outline: none;
        }
    `;
    
    document.head.appendChild(style);
}

/**
 * Add keyboard shortcuts for search
 */
function addSearchKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Only handle keyboard shortcuts when not in an input field
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }
        
        // / key for search
        if (e.key === '/') {
            e.preventDefault();
            const searchInput = document.querySelector('input[name="q"]');
            if (searchInput) {
                searchInput.focus();
            }
        }
    });
}

/**
 * Add search filters for more targeted searching
 */
function addSearchFilters() {
    const searchForm = document.querySelector('.wy-side-nav-search form');
    if (!searchForm) return;
    
    // Create filter container
    const filterContainer = document.createElement('div');
    filterContainer.className = 'search-filters';
    
    // Define search filters
    const filters = [
        { id: 'api', label: 'API' },
        { id: 'examples', label: 'Examples' },
        { id: 'concepts', label: 'Concepts' }
    ];
    
    // Create filter buttons
    filters.forEach(filter => {
        const filterBtn = document.createElement('button');
        filterBtn.type = 'button';
        filterBtn.className = 'search-filter-btn';
        filterBtn.dataset.filter = filter.id;
        filterBtn.textContent = filter.label;
        
        // Add click event
        filterBtn.addEventListener('click', function() {
            // Toggle active state
            this.classList.toggle('active');
            
            // Update search input with filter
            const searchInput = document.querySelector('input[name="q"]');
            if (searchInput) {
                const currentQuery = searchInput.value.trim();
                const filterText = `${filter.id}:`;
                
                // Check if filter is already applied
                if (this.classList.contains('active')) {
                    // Add filter if not already present
                    if (!currentQuery.includes(filterText)) {
                        searchInput.value = `${filterText} ${currentQuery}`;
                    }
                } else {
                    // Remove filter if present
                    searchInput.value = currentQuery.replace(new RegExp(`${filterText}\\s*`, 'g'), '');
                }
                
                // Focus search input
                searchInput.focus();
            }
        });
        
        filterContainer.appendChild(filterBtn);
    });
    
    // Add filter container after search form
    searchForm.appendChild(filterContainer);
    
    // Add styles for search filters
    const style = document.createElement('style');
    style.textContent = `
        .search-filters {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 8px;
        }
        
        .search-filter-btn {
            background-color: var(--primary-light);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 4px 12px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
            color: var(--text-color);
        }
        
        .search-filter-btn:hover {
            background-color: var(--accent-light);
            color: white;
        }
        
        .search-filter-btn.active {
            background-color: var(--accent-color);
            color: white;
            border-color: var(--accent-color);
        }
    `;
    
    document.head.appendChild(style);
}

/**
 * Improve search results display
 */
function improveSearchResults() {
    // This function runs on the search results page
    if (!document.querySelector('.search')) return;
    
    // Add styles for search results
    const style = document.createElement('style');
    style.textContent = `
        .search-results {
            margin-top: 2em;
        }
        
        .search-result {
            margin-bottom: 1.5em;
            padding: 1em;
            border-radius: 4px;
            background-color: var(--primary-light);
            border-left: 4px solid var(--accent-color);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .search-result:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        
        .search-result-title {
            margin-top: 0;
            margin-bottom: 0.5em;
            color: var(--accent-color);
        }
        
        .search-result-title a {
            color: var(--accent-color);
            text-decoration: none;
        }
        
        .search-result-title a:hover {
            text-decoration: underline;
        }
        
        .search-result-path {
            font-size: 0.8em;
            color: var(--text-muted);
            margin-bottom: 0.5em;
        }
        
        .search-result-summary {
            margin-bottom: 0;
        }
        
        .highlighted {
            background-color: rgba(66, 133, 244, 0.2);
            padding: 0 2px;
            border-radius: 2px;
        }
        
        .search-summary {
            margin-bottom: 2em;
            padding: 1em;
            background-color: var(--primary-light);
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .search-count {
            font-weight: bold;
        }
        
        .search-time {
            color: var(--text-muted);
            font-size: 0.9em;
        }
    `;
    
    document.head.appendChild(style);
    
    // Enhance search results after they load
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                enhanceSearchResultsDisplay();
            }
        });
    });
    
    // Start observing the search results container
    const searchResults = document.querySelector('.search');
    if (searchResults) {
        observer.observe(searchResults, { childList: true, subtree: true });
    }
}

/**
 * Enhance the display of search results
 */
function enhanceSearchResultsDisplay() {
    // Get all search result items
    const searchResultItems = document.querySelectorAll('.search li');
    
    searchResultItems.forEach(function(item) {
        // Skip if already enhanced
        if (item.classList.contains('enhanced')) return;
        
        // Mark as enhanced
        item.classList.add('enhanced');
        
        // Get title and link
        const link = item.querySelector('a');
        if (!link) return;
        
        // Create new result container
        const resultContainer = document.createElement('div');
        resultContainer.className = 'search-result';
        
        // Create title
        const title = document.createElement('h3');
        title.className = 'search-result-title';
        title.appendChild(link.cloneNode(true));
        
        // Create path
        const path = document.createElement('div');
        path.className = 'search-result-path';
        path.textContent = link.getAttribute('href');
        
        // Get summary
        const summary = item.querySelector('p');
        let summaryElement = null;
        
        if (summary) {
            summaryElement = document.createElement('p');
            summaryElement.className = 'search-result-summary';
            summaryElement.innerHTML = summary.innerHTML;
        }
        
        // Assemble result
        resultContainer.appendChild(title);
        resultContainer.appendChild(path);
        if (summaryElement) {
            resultContainer.appendChild(summaryElement);
        }
        
        // Replace original item with enhanced version
        item.innerHTML = '';
        item.appendChild(resultContainer);
    });
    
    // Highlight search terms
    highlightSearchTerms();
}

/**
 * Highlight search terms in results
 */
function highlightSearchTerms() {
    // Get search query from URL
    const urlParams = new URLSearchParams(window.location.search);
    const query = urlParams.get('q');
    
    if (!query) return;
    
    // Split query into terms
    const terms = query.toLowerCase().split(/\s+/).filter(term => term.length > 2);
    
    // Get all search result summaries
    const summaries = document.querySelectorAll('.search-result-summary');
    
    summaries.forEach(function(summary) {
        let html = summary.innerHTML;
        
        // Highlight each term
        terms.forEach(function(term) {
            const regex = new RegExp(`(${term})`, 'gi');
            html = html.replace(regex, '<span class="highlighted">$1</span>');
        });
        
        summary.innerHTML = html;
    });
} 