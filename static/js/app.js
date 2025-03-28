document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    // Theme toggling functionality
    const themeToggleBtn = document.getElementById('theme-toggle');
    const darkIcon = document.getElementById('dark-icon');
    const lightIcon = document.getElementById('light-icon');
    const htmlElement = document.documentElement;
    const darkThemeStylesheet = document.getElementById('dark-theme-stylesheet');
    const lightThemeStylesheet = document.getElementById('light-theme-stylesheet');
    
    // Check if user has a saved preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        setTheme(savedTheme);
    }
    
    // Add event listener for theme toggle button
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function() {
            const currentTheme = htmlElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            // Switch theme
            setTheme(newTheme);
            
            // Save preference
            localStorage.setItem('theme', newTheme);
        });
    }
    
    function setTheme(theme) {
        // Set data attribute
        htmlElement.setAttribute('data-bs-theme', theme);
        
        // Toggle stylesheets
        if (theme === 'dark') {
            darkThemeStylesheet.removeAttribute('disabled');
            lightThemeStylesheet.setAttribute('disabled', '');
            
            // Update navbar and footer for dark mode
            document.querySelector('nav').classList.add('navbar-dark', 'bg-dark');
            document.querySelector('nav').classList.remove('navbar-light', 'bg-light');
            document.querySelector('footer').classList.add('bg-dark');
            document.querySelector('footer').classList.remove('bg-light');
        } else {
            darkThemeStylesheet.setAttribute('disabled', '');
            lightThemeStylesheet.removeAttribute('disabled');
            
            // Update navbar and footer for light mode
            document.querySelector('nav').classList.remove('navbar-dark', 'bg-dark');
            document.querySelector('nav').classList.add('navbar-light', 'bg-light');
            document.querySelector('footer').classList.remove('bg-dark');
            document.querySelector('footer').classList.add('bg-light');
        }
        
        // Update icons
        updateThemeIcons(theme);
    }
    
    function updateThemeIcons(theme) {
        if (theme === 'dark') {
            darkIcon.classList.remove('d-none');
            lightIcon.classList.add('d-none');
        } else {
            darkIcon.classList.add('d-none');
            lightIcon.classList.remove('d-none');
        }
    }
    
    // File upload handling
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const urlInput = document.getElementById('url-input');
    const uploadForm = document.getElementById('upload-form');
    const uploadButton = document.getElementById('upload-button');
    const uploadStatus = document.getElementById('upload-status');
    const loadingBackdrop = document.getElementById('loading-backdrop');
    
    // Hide loading backdrop on initial page load
    if (loadingBackdrop) {
        loadingBackdrop.classList.add('d-none');
    }
    
    // Variables for input options and containers
    const urlOption = document.getElementById('url-option');
    const fileOption = document.getElementById('file-option');
    const secOption = document.getElementById('sec-option');
    const urlContainer = document.getElementById('url-container');
    const fileContainer = document.getElementById('file-container');
    const secContainer = document.getElementById('sec-container');
    const secInfo = document.getElementById('sec-info');
    
    // Show SEC EDGAR option by default
    if (secOption && secOption.checked) {
        secContainer.classList.remove('d-none');
        secInfo.classList.remove('d-none');
        fileContainer.classList.add('d-none');
        uploadButton.innerHTML = '<i class="fas fa-search-dollar me-2"></i>Search SEC EDGAR';
    }
    
    // Check if elements exist before adding event listeners
    if (uploadArea) {
        // Drag and drop functionality
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', function() {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                let fileName = fileInput.files[0].name;
                document.getElementById('file-name').textContent = fileName;
                document.getElementById('file-display').classList.remove('d-none');
            }
        });
        
        uploadArea.addEventListener('click', function() {
            fileInput.click();
        });
    }
    
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (fileInput.files.length) {
                let fileName = fileInput.files[0].name;
                document.getElementById('file-name').textContent = fileName;
                document.getElementById('file-display').classList.remove('d-none');
                // Clear URL input since we're uploading a file
                urlInput.value = '';
            }
        });
    }
    
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            const selectedOption = document.querySelector('input[name="upload_type"]:checked').value;
            const companyName = document.getElementById('company-name');
            let isValid = true;
            let errorMessage = '';
            
            // Validate based on selected option
            if (selectedOption === 'file') {
                if (!fileInput.files.length || fileInput.files.length === 0) {
                    isValid = false;
                    errorMessage = 'Please select a PDF file to upload';
                }
            } else if (selectedOption === 'url') {
                if (!urlInput.value || urlInput.value.trim() === '') {
                    isValid = false;
                    errorMessage = 'Please enter a valid URL';
                }
            } else if (selectedOption === 'sec') {
                if (!companyName.value || companyName.value.trim() === '') {
                    isValid = false;
                    errorMessage = 'Please enter a company name to search';
                }
                
                // Change form action for SEC EDGAR search
                if (isValid) {
                    uploadForm.action = `/edgar/search?query=${encodeURIComponent(companyName.value)}`;
                }
            }
            
            if (!isValid) {
                e.preventDefault();
                uploadStatus.textContent = errorMessage;
                uploadStatus.classList.remove('d-none');
                uploadStatus.classList.add('alert-warning');
                return false;
            }
            
            // Show loading backdrop when submitting
            if (loadingBackdrop) {
                loadingBackdrop.classList.remove('d-none');
            }
            
            // Disable upload button to prevent multiple submissions
            uploadButton.disabled = true;
            
            // Set different loading text based on the selected option
            if (selectedOption === 'sec') {
                uploadButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Searching...';
            } else {
                uploadButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
            }
        });
    }
    
    // Toggle between URL, File, and SEC EDGAR options
    
    if (urlOption && fileOption && secOption) {
        urlOption.addEventListener('change', function() {
            if (this.checked) {
                urlContainer.classList.remove('d-none');
                fileContainer.classList.add('d-none');
                secContainer.classList.add('d-none');
                secInfo.classList.add('d-none');
                
                // Clear other inputs
                if (fileInput) fileInput.value = '';
                if (document.getElementById('file-display')) {
                    document.getElementById('file-display').classList.add('d-none');
                }
                if (document.getElementById('company-name')) {
                    document.getElementById('company-name').value = '';
                }
                
                // Update button text
                uploadButton.innerHTML = '<i class="fas fa-search me-2"></i>Analyze with AI';
            }
        });
        
        fileOption.addEventListener('change', function() {
            if (this.checked) {
                fileContainer.classList.remove('d-none');
                urlContainer.classList.add('d-none');
                secContainer.classList.add('d-none');
                secInfo.classList.add('d-none');
                
                // Clear other inputs
                if (urlInput) urlInput.value = '';
                if (document.getElementById('company-name')) {
                    document.getElementById('company-name').value = '';
                }
                
                // Update button text
                uploadButton.innerHTML = '<i class="fas fa-search me-2"></i>Analyze with AI';
            }
        });
        
        secOption.addEventListener('change', function() {
            if (this.checked) {
                secContainer.classList.remove('d-none');
                secInfo.classList.remove('d-none');
                fileContainer.classList.add('d-none');
                urlContainer.classList.add('d-none');
                
                // Clear other inputs
                if (fileInput) fileInput.value = '';
                if (urlInput) urlInput.value = '';
                if (document.getElementById('file-display')) {
                    document.getElementById('file-display').classList.add('d-none');
                }
                
                // Update button text
                uploadButton.innerHTML = '<i class="fas fa-search-dollar me-2"></i>Search SEC EDGAR';
            }
        });
    }
    
    // Check processing status if on insights page
    const insightContainer = document.getElementById('insight-container');
    const documentId = insightContainer?.dataset.documentId;
    const cancelProcessingBtn = document.getElementById('cancel-processing');
    const processingStatus = document.getElementById('processing-status');
    
    // Add event listener for cancel button
    if (cancelProcessingBtn && documentId) {
        cancelProcessingBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to cancel this analysis? This cannot be undone.')) {
                // Display cancellation in progress message
                cancelProcessingBtn.disabled = true;
                cancelProcessingBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Cancelling...';
                
                // Call the cancel API endpoint
                fetch(`/api/processing/${documentId}/cancel`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        // Redirect to home page
                        window.location.href = '/';
                    } else {
                        alert('Error: ' + (data.message || 'Could not cancel processing'));
                        cancelProcessingBtn.disabled = false;
                        cancelProcessingBtn.innerHTML = '<i class="fas fa-stop-circle me-2"></i>Cancel Processing';
                    }
                })
                .catch(error => {
                    console.error('Error cancelling processing:', error);
                    alert('An error occurred while trying to cancel. Please try again.');
                    cancelProcessingBtn.disabled = false;
                    cancelProcessingBtn.innerHTML = '<i class="fas fa-stop-circle me-2"></i>Cancel Processing';
                });
            }
        });
    }
    
    if (documentId && insightContainer) {
        // Keep track of elapsed processing time
        let processingStartTime = new Date();
        let processingTimer;
        
        function updateProcessingTime() {
            if (processingStatus) {
                const elapsedSeconds = Math.floor((new Date() - processingStartTime) / 1000);
                const minutes = Math.floor(elapsedSeconds / 60);
                const seconds = elapsedSeconds % 60;
                processingStatus.textContent = `Analyzing document... (${minutes}m ${seconds}s)`;
            }
            processingTimer = setTimeout(updateProcessingTime, 1000);
        }
        
        // Start the timer if we're on the processing page
        if (processingStatus) {
            updateProcessingTime();
        }
        
        // Function to check processing status
        function checkProcessingStatus() {
            fetch(`/api/processing/${documentId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'completed') {
                        // Clear the timer if it exists
                        if (processingTimer) {
                            clearTimeout(processingTimer);
                        }
                        
                        // Refresh the page to show insights
                        window.location.reload();
                    } else if (data.status === 'failed' || data.status === 'cancelled') {
                        // Clear the timer if it exists
                        if (processingTimer) {
                            clearTimeout(processingTimer);
                        }
                        
                        // Show appropriate message based on status
                        const statusText = data.status === 'cancelled' ? 'Analysis Cancelled' : 'Processing Failed';
                        const iconClass = data.status === 'cancelled' ? 'fa-ban text-warning' : 'fa-exclamation-triangle text-danger';
                        
                        // Show error message
                        insightContainer.innerHTML = `
                            <div class="card mb-4">
                                <div class="card-body text-center">
                                    <i class="fas ${iconClass} fa-3x mb-3"></i>
                                    <h4 class="mb-3">${statusText}</h4>
                                    <p>${data.error || 'The document processing was stopped.'}</p>
                                    <div class="mt-4">
                                        <a href="/" class="btn btn-primary">
                                            <i class="fas fa-home me-2"></i>Return to Home
                                        </a>
                                    </div>
                                </div>
                            </div>`;
                            
                        if (loadingBackdrop) {
                            loadingBackdrop.classList.add('d-none');
                        }
                    } else if (data.status === 'processing' || data.status === 'pending') {
                        // Keep checking status every 5 seconds
                        setTimeout(checkProcessingStatus, 5000);
                    }
                })
                .catch(error => {
                    console.error('Error checking processing status:', error);
                    // Try again after a delay
                    setTimeout(checkProcessingStatus, 8000);
                });
        }
        
        // Start checking status if insights are not loaded yet
        if (document.querySelectorAll('.insight-card').length === 0) {
            checkProcessingStatus();
        } else if (loadingBackdrop) {
            // Hide loading backdrop if insights are already loaded
            loadingBackdrop.classList.add('d-none');
        }
    } else if (loadingBackdrop) {
        // Always hide loading backdrop if not on an insight page with processing
        loadingBackdrop.classList.add('d-none');
    }
});
