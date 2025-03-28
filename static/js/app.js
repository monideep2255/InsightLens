document.addEventListener('DOMContentLoaded', function() {
    // File upload handling
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const urlInput = document.getElementById('url-input');
    const uploadForm = document.getElementById('upload-form');
    const uploadButton = document.getElementById('upload-button');
    const uploadStatus = document.getElementById('upload-status');
    const loadingBackdrop = document.getElementById('loading-backdrop');
    
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
    } else if (loadingBackdrop && !uploadForm) {
        // Hide loading backdrop on pages that don't need it
        loadingBackdrop.classList.add('d-none');
    }
});
