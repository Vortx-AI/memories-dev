// Code Playground for memories-dev documentation
document.addEventListener('DOMContentLoaded', function() {
    // Initialize code playground
    initializeCodePlayground();
});

/**
 * Initialize the code playground component
 */
function initializeCodePlayground() {
    // Find all code playground containers
    const playgroundContainers = document.querySelectorAll('.code-playground');
    
    if (playgroundContainers.length === 0) {
        // Create code playground containers for code examples
        createCodePlaygrounds();
    } else {
        // Initialize existing code playground containers
        playgroundContainers.forEach(container => {
            setupCodePlayground(container);
        });
    }
    
    // Add styles for code playground
    addCodePlaygroundStyles();
}

/**
 * Create code playground containers for code examples
 */
function createCodePlaygrounds() {
    // Find code blocks with playground data attribute
    const codeBlocks = document.querySelectorAll('div.highlight[data-playground="true"]');
    
    // If no code blocks with playground attribute, look for Python code blocks
    if (codeBlocks.length === 0) {
        const pythonCodeBlocks = document.querySelectorAll('div.highlight-python');
        
        pythonCodeBlocks.forEach(block => {
            // Skip very short code blocks
            const code = block.textContent.trim();
            if (code.split('\n').length < 3) return;
            
            // Create playground for this code block
            createPlaygroundForCodeBlock(block, 'python');
        });
    } else {
        // Create playgrounds for marked code blocks
        codeBlocks.forEach(block => {
            // Determine language from class
            const classes = block.className.split(' ');
            let language = 'python';
            
            for (const cls of classes) {
                if (cls.startsWith('highlight-')) {
                    language = cls.replace('highlight-', '');
                    break;
                }
            }
            
            createPlaygroundForCodeBlock(block, language);
        });
    }
}

/**
 * Create a playground for a specific code block
 * @param {HTMLElement} codeBlock - The code block element
 * @param {string} language - The programming language
 */
function createPlaygroundForCodeBlock(codeBlock, language) {
    // Get code content
    const codeElement = codeBlock.querySelector('pre');
    if (!codeElement) return;
    
    const code = codeElement.textContent.trim();
    
    // Create playground container
    const playgroundContainer = document.createElement('div');
    playgroundContainer.className = 'code-playground';
    playgroundContainer.dataset.language = language;
    
    // Create playground header
    const header = document.createElement('div');
    header.className = 'playground-header';
    
    const languageBadge = document.createElement('span');
    languageBadge.className = 'playground-language';
    languageBadge.textContent = language.charAt(0).toUpperCase() + language.slice(1);
    
    const title = document.createElement('span');
    title.className = 'playground-title';
    title.textContent = 'Interactive Example';
    
    const toggleButton = document.createElement('button');
    toggleButton.className = 'playground-toggle';
    toggleButton.innerHTML = '<span>Try it</span><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M1.646 4.646a.5.5 0 0 1 .708 0L8 10.293l5.646-5.647a.5.5 0 0 1 .708.708l-6 6a.5.5 0 0 1-.708 0l-6-6a.5.5 0 0 1 0-.708z"/></svg>';
    
    header.appendChild(languageBadge);
    header.appendChild(title);
    header.appendChild(toggleButton);
    
    // Create playground content
    const content = document.createElement('div');
    content.className = 'playground-content';
    
    // Create editor
    const editor = document.createElement('div');
    editor.className = 'playground-editor';
    
    const editorTextarea = document.createElement('textarea');
    editorTextarea.className = 'playground-code';
    editorTextarea.value = code;
    editorTextarea.setAttribute('spellcheck', 'false');
    editorTextarea.setAttribute('autocomplete', 'off');
    editorTextarea.setAttribute('autocorrect', 'off');
    editorTextarea.setAttribute('autocapitalize', 'off');
    
    editor.appendChild(editorTextarea);
    
    // Create toolbar
    const toolbar = document.createElement('div');
    toolbar.className = 'playground-toolbar';
    
    const runButton = document.createElement('button');
    runButton.className = 'playground-run';
    runButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M11.596 8.697l-6.363 3.692c-.54.313-1.233-.066-1.233-.697V4.308c0-.63.692-1.01 1.233-.696l6.363 3.692a.802.802 0 0 1 0 1.393z"/></svg> Run';
    
    const resetButton = document.createElement('button');
    resetButton.className = 'playground-reset';
    resetButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"/><path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"/></svg> Reset';
    
    const copyButton = document.createElement('button');
    copyButton.className = 'playground-copy';
    copyButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M4 1.5H3a2 2 0 0 0-2 2V14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V3.5a2 2 0 0 0-2-2h-1v1h1a1 1 0 0 1 1 1V14a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V3.5a1 1 0 0 1 1-1h1v-1z"/><path d="M9.5 1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5h3zm-3-1A1.5 1.5 0 0 0 5 1.5v1A1.5 1.5 0 0 0 6.5 4h3A1.5 1.5 0 0 0 11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3z"/></svg> Copy';
    
    toolbar.appendChild(runButton);
    toolbar.appendChild(resetButton);
    toolbar.appendChild(copyButton);
    
    // Create output
    const output = document.createElement('div');
    output.className = 'playground-output';
    
    const outputHeader = document.createElement('div');
    outputHeader.className = 'output-header';
    outputHeader.textContent = 'Output';
    
    const outputContent = document.createElement('pre');
    outputContent.className = 'output-content';
    outputContent.innerHTML = '<code></code>';
    
    output.appendChild(outputHeader);
    output.appendChild(outputContent);
    
    // Assemble content
    content.appendChild(editor);
    content.appendChild(toolbar);
    content.appendChild(output);
    
    // Assemble playground
    playgroundContainer.appendChild(header);
    playgroundContainer.appendChild(content);
    
    // Insert playground after code block
    codeBlock.parentNode.insertBefore(playgroundContainer, codeBlock.nextSibling);
    
    // Setup playground functionality
    setupCodePlayground(playgroundContainer);
    
    // Store original code for reset
    playgroundContainer.dataset.originalCode = code;
}

/**
 * Setup code playground functionality
 * @param {HTMLElement} container - The code playground container
 */
function setupCodePlayground(container) {
    const toggleButton = container.querySelector('.playground-toggle');
    const content = container.querySelector('.playground-content');
    const runButton = container.querySelector('.playground-run');
    const resetButton = container.querySelector('.playground-reset');
    const copyButton = container.querySelector('.playground-copy');
    const codeTextarea = container.querySelector('.playground-code');
    const outputContent = container.querySelector('.output-content code');
    
    // Toggle playground visibility
    toggleButton.addEventListener('click', function() {
        content.classList.toggle('active');
        toggleButton.classList.toggle('active');
    });
    
    // Run code
    runButton.addEventListener('click', function() {
        const code = codeTextarea.value;
        const language = container.dataset.language;
        
        // Show loading state
        runButton.disabled = true;
        runButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"/><path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"/></svg> Running...';
        
        // Execute code (simulated)
        executeCode(code, language)
            .then(result => {
                // Display result
                outputContent.textContent = result;
                
                // Highlight syntax
                if (window.Prism) {
                    Prism.highlightElement(outputContent);
                }
            })
            .catch(error => {
                // Display error
                outputContent.textContent = `Error: ${error.message}`;
                outputContent.classList.add('error');
            })
            .finally(() => {
                // Reset button state
                runButton.disabled = false;
                runButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M11.596 8.697l-6.363 3.692c-.54.313-1.233-.066-1.233-.697V4.308c0-.63.692-1.01 1.233-.696l6.363 3.692a.802.802 0 0 1 0 1.393z"/></svg> Run';
            });
    });
    
    // Reset code
    resetButton.addEventListener('click', function() {
        codeTextarea.value = container.dataset.originalCode;
        outputContent.textContent = '';
        outputContent.classList.remove('error');
    });
    
    // Copy code
    copyButton.addEventListener('click', function() {
        const code = codeTextarea.value;
        
        // Copy to clipboard
        navigator.clipboard.writeText(code).then(() => {
            // Show success state
            copyButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg> Copied!';
            
            // Reset after 2 seconds
            setTimeout(() => {
                copyButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M4 1.5H3a2 2 0 0 0-2 2V14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V3.5a2 2 0 0 0-2-2h-1v1h1a1 1 0 0 1 1 1V14a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V3.5a1 1 0 0 1 1-1h1v-1z"/><path d="M9.5 1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5h3zm-3-1A1.5 1.5 0 0 0 5 1.5v1A1.5 1.5 0 0 0 6.5 4h3A1.5 1.5 0 0 0 11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3z"/></svg> Copy';
            }, 2000);
        });
    });
    
    // Add tab support for code textarea
    codeTextarea.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            e.preventDefault();
            
            // Insert tab at cursor position
            const start = this.selectionStart;
            const end = this.selectionEnd;
            
            this.value = this.value.substring(0, start) + '    ' + this.value.substring(end);
            
            // Move cursor after tab
            this.selectionStart = this.selectionEnd = start + 4;
        }
    });
}

/**
 * Execute code (simulated)
 * @param {string} code - The code to execute
 * @param {string} language - The programming language
 * @returns {Promise} - A promise that resolves with the result
 */
function executeCode(code, language) {
    return new Promise((resolve, reject) => {
        // Simulate execution delay
        setTimeout(() => {
            try {
                // Simulate code execution based on language
                switch (language.toLowerCase()) {
                    case 'python':
                        simulatePythonExecution(code, resolve, reject);
                        break;
                    case 'javascript':
                    case 'js':
                        simulateJavaScriptExecution(code, resolve, reject);
                        break;
                    default:
                        // For other languages, just show a simulation message
                        resolve(`[Simulated ${language} execution output]\n\nCode execution is simulated in this playground.\nIn a real environment, your code would be executed on a server.`);
                }
            } catch (error) {
                reject(error);
            }
        }, 1000);
    });
}

/**
 * Simulate Python code execution
 * @param {string} code - The Python code to execute
 * @param {Function} resolve - The resolve function
 * @param {Function} reject - The reject function
 */
function simulatePythonExecution(code, resolve, reject) {
    // Check for common patterns and simulate output
    
    // Check for print statements
    const printMatches = code.match(/print\s*\((.*?)\)/g);
    if (printMatches && printMatches.length > 0) {
        const output = printMatches.map(match => {
            // Extract content inside print()
            const content = match.match(/print\s*\((.*?)\)/)[1];
            
            // Handle different types of print content
            if (content.startsWith('"') || content.startsWith("'")) {
                // String literal - remove quotes
                return content.replace(/^["']|["']$/g, '');
            } else if (!isNaN(content)) {
                // Number
                return content;
            } else if (content.includes('+')) {
                // Simple addition or concatenation
                const parts = content.split('+').map(p => p.trim());
                if (parts.every(p => !isNaN(p))) {
                    // All parts are numbers, perform addition
                    return parts.reduce((sum, part) => sum + Number(part), 0).toString();
                } else {
                    // String concatenation
                    return parts.map(p => p.replace(/^["']|["']$/g, '')).join('');
                }
            } else {
                // Default case
                return `[Value of ${content}]`;
            }
        }).join('\n');
        
        resolve(output);
        return;
    }
    
    // Check for import statements
    if (code.includes('import ') || code.includes('from ')) {
        resolve("Modules imported successfully.");
        return;
    }
    
    // Check for function definitions
    if (code.includes('def ')) {
        resolve("Function defined successfully.");
        return;
    }
    
    // Check for class definitions
    if (code.includes('class ')) {
        resolve("Class defined successfully.");
        return;
    }
    
    // Default response
    resolve("Code executed successfully. No output to display.");
}

/**
 * Simulate JavaScript code execution
 * @param {string} code - The JavaScript code to execute
 * @param {Function} resolve - The resolve function
 * @param {Function} reject - The reject function
 */
function simulateJavaScriptExecution(code, resolve, reject) {
    // Check for common patterns and simulate output
    
    // Check for console.log statements
    const logMatches = code.match(/console\.log\s*\((.*?)\)/g);
    if (logMatches && logMatches.length > 0) {
        const output = logMatches.map(match => {
            // Extract content inside console.log()
            const content = match.match(/console\.log\s*\((.*?)\)/)[1];
            
            // Handle different types of log content
            if (content.startsWith('"') || content.startsWith("'")) {
                // String literal - remove quotes
                return content.replace(/^["']|["']$/g, '');
            } else if (!isNaN(content)) {
                // Number
                return content;
            } else if (content.includes('+')) {
                // Simple addition or concatenation
                const parts = content.split('+').map(p => p.trim());
                if (parts.every(p => !isNaN(p))) {
                    // All parts are numbers, perform addition
                    return parts.reduce((sum, part) => sum + Number(part), 0).toString();
                } else {
                    // String concatenation
                    return parts.map(p => p.replace(/^["']|["']$/g, '')).join('');
                }
            } else {
                // Default case
                return `[Value of ${content}]`;
            }
        }).join('\n');
        
        resolve(output);
        return;
    }
    
    // Check for function definitions
    if (code.includes('function ')) {
        resolve("Function defined successfully.");
        return;
    }
    
    // Check for class definitions
    if (code.includes('class ')) {
        resolve("Class defined successfully.");
        return;
    }
    
    // Default response
    resolve("Code executed successfully. No output to display.");
}

/**
 * Add styles for code playground
 */
function addCodePlaygroundStyles() {
    const style = document.createElement('style');
    style.textContent = `
        /* Code Playground Styles */
        .code-playground {
            margin: 2rem 0;
            border-radius: 6px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            background-color: var(--primary-light, #2a2a2a);
            border: 1px solid var(--border-color, #3c4043);
        }
        
        .playground-header {
            display: flex;
            align-items: center;
            padding: 1rem;
            background-color: rgba(0, 0, 0, 0.1);
            border-bottom: 1px solid var(--border-color, #3c4043);
        }
        
        .playground-language {
            padding: 0.3rem 0.6rem;
            border-radius: 4px;
            font-weight: bold;
            font-size: 0.8rem;
            margin-right: 1rem;
            background-color: var(--accent-color, #4285f4);
            color: white;
        }
        
        .playground-title {
            flex: 1;
            font-weight: 500;
        }
        
        .playground-toggle {
            background: none;
            border: none;
            color: var(--accent-color, #4285f4);
            cursor: pointer;
            display: flex;
            align-items: center;
            font-size: 0.9rem;
            padding: 0.5rem;
            border-radius: 4px;
            transition: background-color 0.2s;
        }
        
        .playground-toggle:hover {
            background-color: rgba(66, 133, 244, 0.1);
        }
        
        .playground-toggle svg {
            margin-left: 0.5rem;
            transition: transform 0.2s;
        }
        
        .playground-toggle.active svg {
            transform: rotate(180deg);
        }
        
        .playground-content {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }
        
        .playground-content.active {
            max-height: 2000px;
        }
        
        .playground-editor {
            padding: 1rem;
            border-bottom: 1px solid var(--border-color, #3c4043);
        }
        
        .playground-code {
            width: 100%;
            min-height: 150px;
            padding: 1rem;
            border-radius: 4px;
            border: 1px solid var(--border-color, #3c4043);
            background-color: var(--code-bg, #202124);
            color: var(--code-color, #e8eaed);
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 0.9rem;
            line-height: 1.5;
            resize: vertical;
            tab-size: 4;
        }
        
        .playground-code:focus {
            outline: none;
            border-color: var(--accent-color, #4285f4);
            box-shadow: 0 0 0 2px rgba(66, 133, 244, 0.2);
        }
        
        .playground-toolbar {
            display: flex;
            gap: 0.5rem;
            padding: 1rem;
            border-bottom: 1px solid var(--border-color, #3c4043);
        }
        
        .playground-toolbar button {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            border: none;
            font-weight: 500;
            cursor: pointer;
            transition: background-color 0.2s, transform 0.2s;
        }
        
        .playground-run {
            background-color: var(--success-color, #34a853);
            color: white;
        }
        
        .playground-run:hover {
            background-color: #2d9348;
            transform: translateY(-1px);
        }
        
        .playground-reset {
            background-color: var(--warning-color, #fbbc05);
            color: #1a1a1a;
        }
        
        .playground-reset:hover {
            background-color: #e0a800;
            transform: translateY(-1px);
        }
        
        .playground-copy {
            background-color: var(--accent-color, #4285f4);
            color: white;
        }
        
        .playground-copy:hover {
            background-color: var(--accent-dark, #3367d6);
            transform: translateY(-1px);
        }
        
        .playground-toolbar button:disabled {
            background-color: var(--text-muted, #9aa0a6);
            cursor: not-allowed;
            transform: none;
        }
        
        .playground-output {
            padding: 1rem;
        }
        
        .output-header {
            font-weight: 500;
            margin-bottom: 0.5rem;
        }
        
        .output-content {
            background-color: rgba(0, 0, 0, 0.2);
            border-radius: 4px;
            padding: 1rem;
            margin: 0;
            min-height: 50px;
            max-height: 200px;
            overflow: auto;
        }
        
        .output-content code {
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 0.9rem;
            white-space: pre-wrap;
        }
        
        .output-content.error {
            color: var(--danger-color, #ea4335);
        }
        
        /* Responsive styles */
        @media (max-width: 768px) {
            .playground-header {
                flex-direction: column;
                align-items: flex-start;
            }
            
            .playground-language {
                margin-bottom: 0.5rem;
            }
            
            .playground-title {
                margin-bottom: 0.5rem;
            }
            
            .playground-toggle {
                margin-top: 0.5rem;
            }
            
            .playground-toolbar {
                flex-direction: column;
            }
        }
    `;
    
    document.head.appendChild(style);
} 