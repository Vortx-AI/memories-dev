// Feedback Collection System for memories-dev documentation
document.addEventListener('DOMContentLoaded', function() {
    // Initialize feedback collector
    initializeFeedbackCollector();
});

/**
 * Initialize the feedback collection system
 */
function initializeFeedbackCollector() {
    // Add feedback button to each page
    addFeedbackButton();
    
    // Add styles for feedback system
    addFeedbackStyles();
}

/**
 * Add feedback button to the page
 */
function addFeedbackButton() {
    // Create feedback button container
    const feedbackContainer = document.createElement('div');
    feedbackContainer.className = 'feedback-container';
    
    // Create feedback button
    const feedbackButton = document.createElement('button');
    feedbackButton.className = 'feedback-button';
    feedbackButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/><path d="M4.285 12.433a.5.5 0 0 0 .683-.183A3.498 3.498 0 0 1 8 10.5c1.295 0 2.426.703 3.032 1.75a.5.5 0 0 0 .866-.5A4.498 4.498 0 0 0 8 9.5a4.5 4.5 0 0 0-3.898 2.25.5.5 0 0 0 .183.683zM7 6.5C7 7.328 6.552 8 6 8s-1-.672-1-1.5S5.448 5 6 5s1 .672 1 1.5zm4 0c0 .828-.448 1.5-1 1.5s-1-.672-1-1.5S9.448 5 10 5s1 .672 1 1.5z"/></svg> Feedback';
    feedbackButton.setAttribute('aria-label', 'Provide feedback on this page');
    
    // Add click event
    feedbackButton.addEventListener('click', function() {
        showFeedbackForm();
    });
    
    // Add to container
    feedbackContainer.appendChild(feedbackButton);
    
    // Add to page
    const contentArea = document.querySelector('.wy-nav-content');
    if (contentArea) {
        contentArea.appendChild(feedbackContainer);
    } else {
        // Fallback to body if content area not found
        document.body.appendChild(feedbackContainer);
    }
}

/**
 * Show feedback form
 */
function showFeedbackForm() {
    // Create modal container
    const modalContainer = document.createElement('div');
    modalContainer.className = 'feedback-modal-container';
    
    // Create modal content
    const modalContent = document.createElement('div');
    modalContent.className = 'feedback-modal-content';
    
    // Create modal header
    const modalHeader = document.createElement('div');
    modalHeader.className = 'feedback-modal-header';
    
    const modalTitle = document.createElement('h3');
    modalTitle.textContent = 'Documentation Feedback';
    
    const closeButton = document.createElement('button');
    closeButton.className = 'feedback-modal-close';
    closeButton.innerHTML = '&times;';
    closeButton.setAttribute('aria-label', 'Close feedback form');
    
    modalHeader.appendChild(modalTitle);
    modalHeader.appendChild(closeButton);
    
    // Create modal body
    const modalBody = document.createElement('div');
    modalBody.className = 'feedback-modal-body';
    
    // Get current page info
    const currentPage = window.location.pathname;
    const pageTitle = document.title;
    
    modalBody.innerHTML = `
        <p>Your feedback helps us improve the documentation. Please let us know what you think about this page.</p>
        
        <form id="feedback-form">
            <input type="hidden" name="page" value="${currentPage}">
            <input type="hidden" name="title" value="${pageTitle}">
            
            <div class="feedback-field">
                <label>How helpful was this page?</label>
                <div class="feedback-rating">
                    <label class="rating-label">
                        <input type="radio" name="rating" value="1">
                        <span>1</span>
                    </label>
                    <label class="rating-label">
                        <input type="radio" name="rating" value="2">
                        <span>2</span>
                    </label>
                    <label class="rating-label">
                        <input type="radio" name="rating" value="3">
                        <span>3</span>
                    </label>
                    <label class="rating-label">
                        <input type="radio" name="rating" value="4">
                        <span>4</span>
                    </label>
                    <label class="rating-label">
                        <input type="radio" name="rating" value="5" checked>
                        <span>5</span>
                    </label>
                </div>
                <div class="rating-labels">
                    <span>Not helpful</span>
                    <span>Very helpful</span>
                </div>
            </div>
            
            <div class="feedback-field">
                <label for="feedback-type">What kind of feedback do you have?</label>
                <select id="feedback-type" name="feedback_type" required>
                    <option value="">Please select...</option>
                    <option value="suggestion">Suggestion for improvement</option>
                    <option value="error">Error or inaccuracy</option>
                    <option value="missing">Missing information</option>
                    <option value="unclear">Unclear explanation</option>
                    <option value="praise">Positive feedback</option>
                    <option value="other">Other</option>
                </select>
            </div>
            
            <div class="feedback-field">
                <label for="feedback-comments">Comments:</label>
                <textarea id="feedback-comments" name="comments" rows="4" placeholder="Please provide details about your feedback..."></textarea>
            </div>
            
            <div class="feedback-field">
                <label for="feedback-email">Email (optional):</label>
                <input type="email" id="feedback-email" name="email" placeholder="Your email if you'd like us to follow up">
            </div>
        </form>
    `;
    
    // Create modal footer
    const modalFooter = document.createElement('div');
    modalFooter.className = 'feedback-modal-footer';
    
    const submitButton = document.createElement('button');
    submitButton.className = 'feedback-submit';
    submitButton.textContent = 'Submit Feedback';
    
    const cancelButton = document.createElement('button');
    cancelButton.className = 'feedback-cancel';
    cancelButton.textContent = 'Cancel';
    
    modalFooter.appendChild(cancelButton);
    modalFooter.appendChild(submitButton);
    
    // Assemble modal
    modalContent.appendChild(modalHeader);
    modalContent.appendChild(modalBody);
    modalContent.appendChild(modalFooter);
    modalContainer.appendChild(modalContent);
    
    // Add to body
    document.body.appendChild(modalContainer);
    
    // Add event listeners
    closeButton.addEventListener('click', function() {
        modalContainer.remove();
    });
    
    cancelButton.addEventListener('click', function() {
        modalContainer.remove();
    });
    
    submitButton.addEventListener('click', function() {
        submitFeedback(modalContainer);
    });
    
    // Close when clicking outside
    modalContainer.addEventListener('click', function(e) {
        if (e.target === modalContainer) {
            modalContainer.remove();
        }
    });
    
    // Add keyboard support
    modalContainer.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            modalContainer.remove();
        }
    });
    
    // Focus first input
    const firstInput = modalContainer.querySelector('select, textarea');
    if (firstInput) {
        setTimeout(() => {
            firstInput.focus();
        }, 100);
    }
}

/**
 * Submit feedback
 * @param {HTMLElement} modalContainer - The modal container element
 */
function submitFeedback(modalContainer) {
    // Get form data
    const form = document.getElementById('feedback-form');
    const formData = new FormData(form);
    
    // Validate form
    const feedbackType = formData.get('feedback_type');
    if (!feedbackType) {
        showFormError(form, 'Please select a feedback type');
        return;
    }
    
    // Show loading state
    const submitButton = modalContainer.querySelector('.feedback-submit');
    const originalText = submitButton.textContent;
    submitButton.disabled = true;
    submitButton.textContent = 'Submitting...';
    
    // In a real implementation, you would send this data to a server
    // For this example, we'll simulate a successful submission
    setTimeout(function() {
        // Show success message
        const modalBody = modalContainer.querySelector('.feedback-modal-body');
        modalBody.innerHTML = `
            <div class="feedback-success">
                <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
                </svg>
                <h3>Thank You!</h3>
                <p>Your feedback has been submitted successfully. We appreciate your input and will use it to improve our documentation.</p>
            </div>
        `;
        
        // Update footer
        const modalFooter = modalContainer.querySelector('.feedback-modal-footer');
        modalFooter.innerHTML = `
            <button class="feedback-close">Close</button>
        `;
        
        // Add event listener to close button
        modalContainer.querySelector('.feedback-close').addEventListener('click', function() {
            modalContainer.remove();
        });
        
        // Store in localStorage that user has provided feedback
        localStorage.setItem('feedback_provided', 'true');
        localStorage.setItem('feedback_provided_date', new Date().toISOString());
        
        // Log feedback data (in a real implementation, this would be sent to a server)
        console.log('Feedback submitted:', Object.fromEntries(formData.entries()));
    }, 1500);
}

/**
 * Show form error
 * @param {HTMLElement} form - The form element
 * @param {string} message - The error message
 */
function showFormError(form, message) {
    // Remove existing error
    const existingError = form.querySelector('.feedback-error');
    if (existingError) {
        existingError.remove();
    }
    
    // Create error message
    const errorElement = document.createElement('div');
    errorElement.className = 'feedback-error';
    errorElement.textContent = message;
    
    // Add to form
    form.insertBefore(errorElement, form.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(function() {
        if (form.contains(errorElement)) {
            errorElement.remove();
        }
    }, 5000);
}

/**
 * Add styles for feedback system
 */
function addFeedbackStyles() {
    const style = document.createElement('style');
    style.textContent = `
        /* Feedback Button */
        .feedback-container {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 100;
        }
        
        .feedback-button {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 16px;
            background-color: var(--accent-color, #4285f4);
            color: white;
            border: none;
            border-radius: 20px;
            cursor: pointer;
            font-weight: 500;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
            transition: all 0.2s ease-in-out;
        }
        
        .feedback-button:hover {
            background-color: var(--accent-dark, #3367d6);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }
        
        .feedback-button svg {
            flex-shrink: 0;
        }
        
        /* Feedback Modal */
        .feedback-modal-container {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            padding: 20px;
        }
        
        .feedback-modal-content {
            background-color: var(--primary-light, #f8f9fa);
            border-radius: 8px;
            width: 100%;
            max-width: 500px;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
            display: flex;
            flex-direction: column;
        }
        
        .feedback-modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 20px;
            border-bottom: 1px solid var(--border-color, #dadce0);
        }
        
        .feedback-modal-header h3 {
            margin: 0;
            font-size: 18px;
            color: var(--text-color, #202124);
        }
        
        .feedback-modal-close {
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: var(--text-muted, #5f6368);
            padding: 0;
            line-height: 1;
        }
        
        .feedback-modal-body {
            padding: 20px;
            flex: 1;
            overflow-y: auto;
        }
        
        .feedback-modal-footer {
            display: flex;
            justify-content: flex-end;
            gap: 12px;
            padding: 16px 20px;
            border-top: 1px solid var(--border-color, #dadce0);
        }
        
        /* Form Styles */
        .feedback-field {
            margin-bottom: 16px;
        }
        
        .feedback-field label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: var(--text-color, #202124);
        }
        
        .feedback-field input[type="text"],
        .feedback-field input[type="email"],
        .feedback-field select,
        .feedback-field textarea {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid var(--border-color, #dadce0);
            border-radius: 4px;
            font-size: 14px;
            background-color: var(--primary-color, #ffffff);
            color: var(--text-color, #202124);
        }
        
        .feedback-field input[type="text"]:focus,
        .feedback-field input[type="email"]:focus,
        .feedback-field select:focus,
        .feedback-field textarea:focus {
            outline: none;
            border-color: var(--accent-color, #4285f4);
            box-shadow: 0 0 0 2px rgba(66, 133, 244, 0.2);
        }
        
        /* Rating */
        .feedback-rating {
            display: flex;
            gap: 8px;
            margin-bottom: 4px;
        }
        
        .rating-label {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            border-radius: 4px;
            cursor: pointer;
            background-color: var(--primary-color, #ffffff);
            border: 1px solid var(--border-color, #dadce0);
            transition: all 0.2s;
        }
        
        .rating-label:hover {
            background-color: var(--accent-light, #5c9aff);
            color: white;
            border-color: var(--accent-light, #5c9aff);
        }
        
        .rating-label input {
            position: absolute;
            opacity: 0;
            width: 0;
            height: 0;
        }
        
        .rating-label input:checked + span {
            font-weight: bold;
        }
        
        .rating-label input:checked ~ .rating-label {
            background-color: var(--accent-color, #4285f4);
            color: white;
            border-color: var(--accent-color, #4285f4);
        }
        
        .rating-labels {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: var(--text-muted, #5f6368);
        }
        
        /* Buttons */
        .feedback-submit,
        .feedback-cancel,
        .feedback-close {
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 500;
            font-size: 14px;
        }
        
        .feedback-submit {
            background-color: var(--accent-color, #4285f4);
            color: white;
            border: none;
        }
        
        .feedback-submit:hover {
            background-color: var(--accent-dark, #3367d6);
        }
        
        .feedback-submit:disabled {
            background-color: var(--text-muted, #9aa0a6);
            cursor: not-allowed;
        }
        
        .feedback-cancel,
        .feedback-close {
            background-color: transparent;
            color: var(--text-color, #202124);
            border: 1px solid var(--border-color, #dadce0);
        }
        
        .feedback-cancel:hover,
        .feedback-close:hover {
            background-color: var(--primary-dark, #e9ecef);
        }
        
        /* Error Message */
        .feedback-error {
            background-color: rgba(234, 67, 53, 0.1);
            color: #ea4335;
            padding: 8px 12px;
            border-radius: 4px;
            margin-bottom: 16px;
            font-size: 14px;
            border-left: 3px solid #ea4335;
        }
        
        /* Success Message */
        .feedback-success {
            text-align: center;
            padding: 20px 0;
            color: var(--success-color, #34a853);
        }
        
        .feedback-success svg {
            margin-bottom: 16px;
            color: var(--success-color, #34a853);
        }
        
        .feedback-success h3 {
            margin-top: 0;
            margin-bottom: 8px;
            color: var(--text-color, #202124);
        }
        
        .feedback-success p {
            color: var(--text-muted, #5f6368);
            margin-bottom: 0;
        }
        
        /* Responsive styles */
        @media (max-width: 768px) {
            .feedback-container {
                bottom: 10px;
                right: 10px;
            }
            
            .feedback-button {
                padding: 8px 12px;
                font-size: 13px;
            }
            
            .feedback-modal-content {
                max-width: 100%;
            }
            
            .feedback-rating {
                gap: 4px;
            }
            
            .rating-label {
                width: 36px;
                height: 36px;
            }
        }
    `;
    
    document.head.appendChild(style);
} 