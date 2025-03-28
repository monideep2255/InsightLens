document.addEventListener('DOMContentLoaded', function() {
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
            // Validate either file or URL is provided
            if ((!fileInput.files.length || fileInput.files.length === 0) && 
                (!urlInput.value || urlInput.value.trim() === '')) {
                e.preventDefault();
                uploadStatus.textContent = 'Please provide either a PDF file or URL';
                uploadStatus.classList.remove('d-none');
                uploadStatus.classList.add('text-danger');
                return false;
            }
            
            // Show loading backdrop when submitting
            if (loadingBackdrop) {
                loadingBackdrop.classList.remove('d-none');
            }
            
            // Disable upload button to prevent multiple submissions
            uploadButton.disabled = true;
            uploadButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
        });
    }
    
    // Toggle between URL and File inputs
    const urlOption = document.getElementById('url-option');
    const fileOption = document.getElementById('file-option');
    const urlContainer = document.getElementById('url-container');
    const fileContainer = document.getElementById('file-container');
    
    if (urlOption && fileOption) {
        urlOption.addEventListener('change', function() {
            if (this.checked) {
                urlContainer.classList.remove('d-none');
                fileContainer.classList.add('d-none');
                // Clear file input
                if (fileInput) fileInput.value = '';
                if (document.getElementById('file-display')) {
                    document.getElementById('file-display').classList.add('d-none');
                }
            }
        });
        
        fileOption.addEventListener('change', function() {
            if (this.checked) {
                fileContainer.classList.remove('d-none');
                urlContainer.classList.add('d-none');
                // Clear URL input
                if (urlInput) urlInput.value = '';
            }
        });
    }
    
    // Check processing status if on insights page
    const insightContainer = document.getElementById('insight-container');
    const documentId = insightContainer?.dataset.documentId;
    
    if (documentId && insightContainer) {
        // Function to check processing status
        function checkProcessingStatus() {
            fetch(`/api/processing/${documentId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'completed') {
                        // Refresh the page to show insights
                        window.location.reload();
                    } else if (data.status === 'failed') {
                        // Show error message
                        insightContainer.innerHTML = `
                            <div class="alert alert-danger" role="alert">
                                <h4 class="alert-heading">Processing Failed!</h4>
                                <p>${data.error || 'An error occurred while processing your document.'}</p>
                                <hr>
                                <p class="mb-0">Please try uploading a different document or check the URL.</p>
                            </div>`;
                        if (loadingBackdrop) {
                            loadingBackdrop.classList.add('d-none');
                        }
                    } else if (data.status === 'processing' || data.status === 'pending') {
                        // Keep checking status every 3 seconds
                        setTimeout(checkProcessingStatus, 3000);
                    }
                })
                .catch(error => {
                    console.error('Error checking processing status:', error);
                    // Try again after a delay
                    setTimeout(checkProcessingStatus, 5000);
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
