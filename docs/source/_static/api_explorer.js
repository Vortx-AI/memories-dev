// Interactive API Explorer for memories-dev documentation
document.addEventListener('DOMContentLoaded', function() {
    // Initialize API explorer
    initializeApiExplorer();
});

/**
 * Initialize the API explorer component
 */
function initializeApiExplorer() {
    // Find all API explorer containers
    const apiExplorerContainers = document.querySelectorAll('.api-explorer');
    
    if (apiExplorerContainers.length === 0) {
        // Create API explorer containers for API reference pages
        createApiExplorers();
    } else {
        // Initialize existing API explorer containers
        apiExplorerContainers.forEach(container => {
            setupApiExplorer(container);
        });
    }
    
    // Add styles for API explorer
    addApiExplorerStyles();
}

/**
 * Create API explorer containers for API reference pages
 */
function createApiExplorers() {
    // Find API reference sections
    const apiSections = document.querySelectorAll('.section[id^="api-"]');
    
    apiSections.forEach(section => {
        // Get API details
        const apiTitle = section.querySelector('h2, h3')?.textContent || 'API Endpoint';
        const apiDescription = section.querySelector('p')?.textContent || 'No description available';
        const apiEndpoint = extractEndpoint(section);
        const apiMethod = extractMethod(section);
        const apiParams = extractParameters(section);
        
        // Create API explorer container
        const explorerContainer = document.createElement('div');
        explorerContainer.className = 'api-explorer';
        explorerContainer.dataset.endpoint = apiEndpoint;
        explorerContainer.dataset.method = apiMethod;
        
        // Create explorer header
        const header = document.createElement('div');
        header.className = 'api-explorer-header';
        
        const methodBadge = document.createElement('span');
        methodBadge.className = `api-method api-method-${apiMethod.toLowerCase()}`;
        methodBadge.textContent = apiMethod;
        
        const endpointDisplay = document.createElement('code');
        endpointDisplay.className = 'api-endpoint';
        endpointDisplay.textContent = apiEndpoint;
        
        const toggleButton = document.createElement('button');
        toggleButton.className = 'api-explorer-toggle';
        toggleButton.innerHTML = '<span>Try it</span><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M1.646 4.646a.5.5 0 0 1 .708 0L8 10.293l5.646-5.647a.5.5 0 0 1 .708.708l-6 6a.5.5 0 0 1-.708 0l-6-6a.5.5 0 0 1 0-.708z"/></svg>';
        
        header.appendChild(methodBadge);
        header.appendChild(endpointDisplay);
        header.appendChild(toggleButton);
        
        // Create explorer content
        const content = document.createElement('div');
        content.className = 'api-explorer-content';
        
        // Create parameters form
        const paramsForm = document.createElement('form');
        paramsForm.className = 'api-params-form';
        
        // Add parameters to form
        apiParams.forEach(param => {
            const paramGroup = document.createElement('div');
            paramGroup.className = 'api-param-group';
            
            const paramLabel = document.createElement('label');
            paramLabel.htmlFor = `param-${param.name}`;
            paramLabel.textContent = param.name;
            
            if (param.required) {
                const requiredBadge = document.createElement('span');
                requiredBadge.className = 'api-param-required';
                requiredBadge.textContent = 'Required';
                paramLabel.appendChild(requiredBadge);
            }
            
            const paramInput = document.createElement('input');
            paramInput.type = 'text';
            paramInput.id = `param-${param.name}`;
            paramInput.name = param.name;
            paramInput.placeholder = param.description || param.name;
            paramInput.dataset.required = param.required;
            
            const paramDescription = document.createElement('div');
            paramDescription.className = 'api-param-description';
            paramDescription.textContent = param.description || '';
            
            paramGroup.appendChild(paramLabel);
            paramGroup.appendChild(paramInput);
            paramGroup.appendChild(paramDescription);
            
            paramsForm.appendChild(paramGroup);
        });
        
        // Create execute button
        const executeButton = document.createElement('button');
        executeButton.type = 'submit';
        executeButton.className = 'api-execute-button';
        executeButton.textContent = 'Execute Request';
        
        paramsForm.appendChild(executeButton);
        
        // Create response section
        const responseSection = document.createElement('div');
        responseSection.className = 'api-response-section';
        
        const responseHeader = document.createElement('div');
        responseHeader.className = 'api-response-header';
        responseHeader.innerHTML = '<h4>Response</h4><div class="api-response-status"></div>';
        
        const responseBody = document.createElement('pre');
        responseBody.className = 'api-response-body';
        responseBody.innerHTML = '<code></code>';
        
        responseSection.appendChild(responseHeader);
        responseSection.appendChild(responseBody);
        
        // Assemble content
        content.appendChild(paramsForm);
        content.appendChild(responseSection);
        
        // Assemble explorer
        explorerContainer.appendChild(header);
        explorerContainer.appendChild(content);
        
        // Add explorer to section
        section.appendChild(explorerContainer);
        
        // Setup explorer functionality
        setupApiExplorer(explorerContainer);
    });
}

/**
 * Setup API explorer functionality
 * @param {HTMLElement} container - The API explorer container
 */
function setupApiExplorer(container) {
    const toggleButton = container.querySelector('.api-explorer-toggle');
    const content = container.querySelector('.api-explorer-content');
    const form = container.querySelector('.api-params-form');
    const responseStatus = container.querySelector('.api-response-status');
    const responseBody = container.querySelector('.api-response-body code');
    
    // Toggle explorer visibility
    toggleButton.addEventListener('click', function() {
        content.classList.toggle('active');
        toggleButton.classList.toggle('active');
    });
    
    // Handle form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Validate required fields
        const requiredInputs = form.querySelectorAll('input[data-required="true"]');
        let isValid = true;
        
        requiredInputs.forEach(input => {
            if (!input.value.trim()) {
                input.classList.add('error');
                isValid = false;
            } else {
                input.classList.remove('error');
            }
        });
        
        if (!isValid) {
            responseStatus.textContent = 'Error: Please fill in all required fields';
            responseStatus.className = 'api-response-status error';
            return;
        }
        
        // Show loading state
        const executeButton = form.querySelector('.api-execute-button');
        executeButton.disabled = true;
        executeButton.textContent = 'Loading...';
        
        responseStatus.textContent = 'Sending request...';
        responseStatus.className = 'api-response-status loading';
        
        // Get form data
        const formData = new FormData(form);
        const params = {};
        
        for (const [key, value] of formData.entries()) {
            if (value.trim()) {
                params[key] = value;
            }
        }
        
        // Get API details
        const endpoint = container.dataset.endpoint;
        const method = container.dataset.method;
        
        // Simulate API request (replace with actual API call in production)
        simulateApiRequest(endpoint, method, params)
            .then(response => {
                // Update response display
                responseStatus.textContent = `Status: ${response.status}`;
                responseStatus.className = 'api-response-status success';
                
                // Format and display response body
                const formattedJson = JSON.stringify(response.data, null, 2);
                responseBody.textContent = formattedJson;
                
                // Highlight syntax
                if (window.Prism) {
                    Prism.highlightElement(responseBody);
                }
            })
            .catch(error => {
                // Display error
                responseStatus.textContent = `Error: ${error.message}`;
                responseStatus.className = 'api-response-status error';
                
                // Format and display error details
                const errorDetails = error.details || { message: error.message };
                const formattedJson = JSON.stringify(errorDetails, null, 2);
                responseBody.textContent = formattedJson;
                
                // Highlight syntax
                if (window.Prism) {
                    Prism.highlightElement(responseBody);
                }
            })
            .finally(() => {
                // Reset button state
                executeButton.disabled = false;
                executeButton.textContent = 'Execute Request';
            });
    });
}

/**
 * Simulate an API request (replace with actual API call in production)
 * @param {string} endpoint - The API endpoint
 * @param {string} method - The HTTP method
 * @param {Object} params - The request parameters
 * @returns {Promise} - A promise that resolves with the response
 */
function simulateApiRequest(endpoint, method, params) {
    return new Promise((resolve, reject) => {
        // Simulate network delay
        setTimeout(() => {
            // Simulate successful response
            if (Math.random() > 0.2) {
                resolve({
                    status: 200,
                    data: {
                        success: true,
                        endpoint: endpoint,
                        method: method,
                        params: params,
                        result: {
                            id: Math.floor(Math.random() * 1000),
                            timestamp: new Date().toISOString(),
                            data: "Sample response data"
                        }
                    }
                });
            } else {
                // Simulate error response
                reject({
                    message: "Request failed",
                    details: {
                        error: "sample_error",
                        message: "This is a simulated error response",
                        endpoint: endpoint,
                        method: method,
                        params: params
                    }
                });
            }
        }, 1000);
    });
}

/**
 * Extract API endpoint from section content
 * @param {HTMLElement} section - The API section element
 * @returns {string} - The extracted endpoint
 */
function extractEndpoint(section) {
    // Try to find endpoint in code blocks or specific elements
    const codeBlocks = section.querySelectorAll('code');
    for (const code of codeBlocks) {
        const text = code.textContent;
        if (text.startsWith('/') || text.includes('api/')) {
            return text.trim();
        }
    }
    
    // Fallback: use section ID
    return `/api/${section.id.replace('api-', '')}`;
}

/**
 * Extract API method from section content
 * @param {HTMLElement} section - The API section element
 * @returns {string} - The extracted method
 */
function extractMethod(section) {
    // Look for method keywords in the section
    const content = section.textContent.toLowerCase();
    
    if (content.includes('post ') || content.includes('method="post"') || content.includes('method: post')) {
        return 'POST';
    } else if (content.includes('put ') || content.includes('method="put"') || content.includes('method: put')) {
        return 'PUT';
    } else if (content.includes('delete ') || content.includes('method="delete"') || content.includes('method: delete')) {
        return 'DELETE';
    } else if (content.includes('patch ') || content.includes('method="patch"') || content.includes('method: patch')) {
        return 'PATCH';
    }
    
    // Default to GET
    return 'GET';
}

/**
 * Extract API parameters from section content
 * @param {HTMLElement} section - The API section element
 * @returns {Array} - The extracted parameters
 */
function extractParameters(section) {
    const params = [];
    
    // Look for parameter tables
    const tables = section.querySelectorAll('table');
    
    tables.forEach(table => {
        // Check if this looks like a parameters table
        const headerRow = table.querySelector('thead tr');
        if (!headerRow) return;
        
        const headerCells = headerRow.querySelectorAll('th');
        const headerTexts = Array.from(headerCells).map(cell => cell.textContent.toLowerCase());
        
        // Check if this table has parameter-like headers
        const hasParamHeader = headerTexts.some(text => 
            text.includes('parameter') || text.includes('param') || text.includes('name')
        );
        
        if (!hasParamHeader) return;
        
        // Extract parameters from rows
        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length < 2) return;
            
            const name = cells[0].textContent.trim();
            const description = cells[1].textContent.trim();
            const required = cells.length > 2 ? 
                cells[2].textContent.toLowerCase().includes('required') : 
                false;
            
            params.push({
                name,
                description,
                required
            });
        });
    });
    
    // If no parameters found in tables, look for lists
    if (params.length === 0) {
        const lists = section.querySelectorAll('ul, ol');
        
        lists.forEach(list => {
            const items = list.querySelectorAll('li');
            
            items.forEach(item => {
                const text = item.textContent;
                
                // Try to extract parameter name and description
                const match = text.match(/^([a-zA-Z0-9_]+)(?:\s*\(([^)]+)\))?\s*(?:-|:)\s*(.+)$/);
                
                if (match) {
                    const name = match[1].trim();
                    const type = match[2] ? match[2].trim() : '';
                    const description = match[3].trim();
                    const required = text.toLowerCase().includes('required');
                    
                    params.push({
                        name,
                        description: type ? `${description} (${type})` : description,
                        required
                    });
                }
            });
        });
    }
    
    // Add some default parameters if none found
    if (params.length === 0) {
        params.push(
            { name: 'api_key', description: 'Your API key for authentication', required: true },
            { name: 'format', description: 'Response format (json, xml)', required: false }
        );
    }
    
    return params;
}

/**
 * Add styles for API explorer
 */
function addApiExplorerStyles() {
    const style = document.createElement('style');
    style.textContent = `
        /* API Explorer Styles */
        .api-explorer {
            margin: 2rem 0;
            border-radius: 6px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            background-color: var(--primary-light, #2a2a2a);
            border: 1px solid var(--border-color, #3c4043);
        }
        
        .api-explorer-header {
            display: flex;
            align-items: center;
            padding: 1rem;
            background-color: rgba(0, 0, 0, 0.1);
            border-bottom: 1px solid var(--border-color, #3c4043);
        }
        
        .api-method {
            padding: 0.3rem 0.6rem;
            border-radius: 4px;
            font-weight: bold;
            font-size: 0.8rem;
            margin-right: 1rem;
            text-transform: uppercase;
        }
        
        .api-method-get {
            background-color: #34a853;
            color: white;
        }
        
        .api-method-post {
            background-color: #4285f4;
            color: white;
        }
        
        .api-method-put {
            background-color: #fbbc05;
            color: #1a1a1a;
        }
        
        .api-method-delete {
            background-color: #ea4335;
            color: white;
        }
        
        .api-method-patch {
            background-color: #9334e6;
            color: white;
        }
        
        .api-endpoint {
            flex: 1;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 0.9rem;
            padding: 0.3rem 0.6rem;
            background-color: rgba(0, 0, 0, 0.2);
            border-radius: 4px;
            overflow-x: auto;
            white-space: nowrap;
        }
        
        .api-explorer-toggle {
            background: none;
            border: none;
            color: var(--accent-color, #4285f4);
            cursor: pointer;
            display: flex;
            align-items: center;
            font-size: 0.9rem;
            padding: 0.5rem;
            margin-left: 1rem;
            border-radius: 4px;
            transition: background-color 0.2s;
        }
        
        .api-explorer-toggle:hover {
            background-color: rgba(66, 133, 244, 0.1);
        }
        
        .api-explorer-toggle svg {
            margin-left: 0.5rem;
            transition: transform 0.2s;
        }
        
        .api-explorer-toggle.active svg {
            transform: rotate(180deg);
        }
        
        .api-explorer-content {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }
        
        .api-explorer-content.active {
            max-height: 2000px;
        }
        
        .api-params-form {
            padding: 1rem;
            border-bottom: 1px solid var(--border-color, #3c4043);
        }
        
        .api-param-group {
            margin-bottom: 1rem;
        }
        
        .api-param-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }
        
        .api-param-required {
            font-size: 0.7rem;
            background-color: var(--accent-color, #4285f4);
            color: white;
            padding: 0.1rem 0.4rem;
            border-radius: 3px;
            margin-left: 0.5rem;
            vertical-align: middle;
        }
        
        .api-param-group input {
            width: 100%;
            padding: 0.6rem;
            border-radius: 4px;
            border: 1px solid var(--border-color, #3c4043);
            background-color: rgba(0, 0, 0, 0.2);
            color: var(--text-color, #e8eaed);
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 0.9rem;
        }
        
        .api-param-group input:focus {
            outline: none;
            border-color: var(--accent-color, #4285f4);
            box-shadow: 0 0 0 2px rgba(66, 133, 244, 0.2);
        }
        
        .api-param-group input.error {
            border-color: var(--danger-color, #ea4335);
            box-shadow: 0 0 0 2px rgba(234, 67, 53, 0.2);
        }
        
        .api-param-description {
            font-size: 0.8rem;
            color: var(--text-muted, #9aa0a6);
            margin-top: 0.3rem;
        }
        
        .api-execute-button {
            background-color: var(--accent-color, #4285f4);
            color: white;
            border: none;
            padding: 0.7rem 1.2rem;
            border-radius: 4px;
            font-weight: 500;
            cursor: pointer;
            transition: background-color 0.2s, transform 0.2s;
            margin-top: 1rem;
        }
        
        .api-execute-button:hover {
            background-color: var(--accent-dark, #3367d6);
            transform: translateY(-1px);
        }
        
        .api-execute-button:disabled {
            background-color: var(--text-muted, #9aa0a6);
            cursor: not-allowed;
            transform: none;
        }
        
        .api-response-section {
            padding: 1rem;
        }
        
        .api-response-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        
        .api-response-header h4 {
            margin: 0;
            font-size: 1rem;
        }
        
        .api-response-status {
            font-size: 0.9rem;
            padding: 0.3rem 0.6rem;
            border-radius: 4px;
            background-color: rgba(0, 0, 0, 0.2);
        }
        
        .api-response-status.success {
            color: var(--success-color, #34a853);
        }
        
        .api-response-status.error {
            color: var(--danger-color, #ea4335);
        }
        
        .api-response-status.loading {
            color: var(--warning-color, #fbbc05);
        }
        
        .api-response-body {
            background-color: rgba(0, 0, 0, 0.2);
            border-radius: 4px;
            padding: 1rem;
            margin: 0;
            max-height: 300px;
            overflow: auto;
        }
        
        .api-response-body code {
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 0.9rem;
            white-space: pre;
        }
        
        /* Responsive styles */
        @media (max-width: 768px) {
            .api-explorer-header {
                flex-direction: column;
                align-items: flex-start;
            }
            
            .api-method {
                margin-bottom: 0.5rem;
            }
            
            .api-endpoint {
                width: 100%;
                margin-bottom: 0.5rem;
            }
            
            .api-explorer-toggle {
                margin-left: 0;
                margin-top: 0.5rem;
            }
        }
    `;
    
    document.head.appendChild(style);
} 