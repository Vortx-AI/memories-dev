// Version Selector for memories-dev documentation
document.addEventListener('DOMContentLoaded', function() {
    // Initialize version selector
    initializeVersionSelector();
});

/**
 * Initialize the version selector component
 */
function initializeVersionSelector() {
    // Add version selector to the page
    addVersionSelector();
    
    // Add styles for version selector
    addVersionSelectorStyles();
}

/**
 * Add version selector to the page
 */
function addVersionSelector() {
    // Get versions (in a real implementation, this would be populated from a versions.json file)
    const versions = getAvailableVersions();
    
    // Create version selector container
    const selectorContainer = document.createElement('div');
    selectorContainer.className = 'version-selector-container';
    selectorContainer.setAttribute('aria-label', 'Documentation version selector');
    
    // Create version selector
    const selectorLabel = document.createElement('span');
    selectorLabel.className = 'version-selector-label';
    selectorLabel.textContent = 'Version:';
    
    const selector = document.createElement('select');
    selector.className = 'version-selector';
    selector.setAttribute('aria-label', 'Select documentation version');
    
    // Add versions to selector
    versions.forEach(version => {
        const option = document.createElement('option');
        option.value = version.url;
        option.textContent = version.label;
        
        // Set current version as selected
        if (version.current) {
            option.selected = true;
        }
        
        selector.appendChild(option);
    });
    
    // Add event listener to handle version change
    selector.addEventListener('change', function() {
        const selectedUrl = this.value;
        if (selectedUrl) {
            // Show confirmation if switching to a different version
            if (confirm('You are about to switch to a different version of the documentation. Continue?')) {
                window.location.href = selectedUrl;
            } else {
                // Reset to current version if user cancels
                const currentOption = Array.from(this.options).find(option => 
                    option.selected && option.parentElement.querySelector('option[selected]') === option
                );
                if (currentOption) {
                    this.value = currentOption.value;
                }
            }
        }
    });
    
    // Assemble selector
    selectorContainer.appendChild(selectorLabel);
    selectorContainer.appendChild(selector);
    
    // Add to page
    const versionArea = document.querySelector('.wy-side-nav-search');
    if (versionArea) {
        // Insert after the search box
        const searchBox = versionArea.querySelector('.wy-form');
        if (searchBox) {
            versionArea.insertBefore(selectorContainer, searchBox.nextSibling);
        } else {
            versionArea.appendChild(selectorContainer);
        }
    } else {
        // Fallback: Add to body
        document.body.appendChild(selectorContainer);
    }
}

/**
 * Get available documentation versions
 * @returns {Array} - Array of version objects
 */
function getAvailableVersions() {
    // Try to get versions from meta tag
    const metaVersions = document.querySelector('meta[name="documentation-versions"]');
    if (metaVersions) {
        try {
            return JSON.parse(metaVersions.getAttribute('content'));
        } catch (e) {
            console.error('Error parsing documentation versions:', e);
        }
    }
    
    // Fallback: Return simulated versions
    // In a real implementation, this would be populated from a versions.json file
    return [
        {
            label: 'Latest (dev)',
            url: '#',
            current: true
        },
        {
            label: 'v1.0.0 (stable)',
            url: '/v1.0.0/'
        },
        {
            label: 'v0.9.0',
            url: '/v0.9.0/'
        },
        {
            label: 'v0.8.0',
            url: '/v0.8.0/'
        }
    ];
}

/**
 * Add styles for version selector
 */
function addVersionSelectorStyles() {
    const style = document.createElement('style');
    style.textContent = `
        /* Version Selector Container */
        .version-selector-container {
            display: flex;
            align-items: center;
            margin: 1rem 0;
            padding: 0 1rem;
        }
        
        /* Version Selector Label */
        .version-selector-label {
            font-size: 14px;
            font-weight: 500;
            color: rgba(255, 255, 255, 0.8);
            margin-right: 0.5rem;
        }
        
        /* Version Selector */
        .version-selector {
            flex: 1;
            padding: 0.5rem;
            border-radius: 4px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            background-color: rgba(255, 255, 255, 0.1);
            color: white;
            font-size: 14px;
            cursor: pointer;
            appearance: none;
            -webkit-appearance: none;
            -moz-appearance: none;
            background-image: url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='white' viewBox='0 0 16 16'%3E%3Cpath fill-rule='evenodd' d='M1.646 4.646a.5.5 0 0 1 .708 0L8 10.293l5.646-5.647a.5.5 0 0 1 .708.708l-6 6a.5.5 0 0 1-.708 0l-6-6a.5.5 0 0 1 0-.708z'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 0.5rem center;
            padding-right: 2rem;
        }
        
        .version-selector:hover {
            background-color: rgba(255, 255, 255, 0.2);
        }
        
        .version-selector:focus {
            outline: none;
            box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.4);
        }
        
        /* Version Selector Options */
        .version-selector option {
            background-color: var(--background-color, #1a1a1a);
            color: var(--text-color, #f8f9fa);
        }
        
        /* Responsive styles */
        @media (max-width: 768px) {
            .version-selector-container {
                flex-direction: column;
                align-items: flex-start;
            }
            
            .version-selector-label {
                margin-bottom: 0.5rem;
            }
            
            .version-selector {
                width: 100%;
            }
        }
    `;
    
    document.head.appendChild(style);
} 