$(document).ready(function() {
    let pollingInterval;
    const progressBar = $('#progressBar');
    const progressText = $('#progressText');
    const progressDetails = $('#progressDetails');
    const progressContainer = $('#progressContainer');
    const runningAlert = $('#runningAlert');
    const successAlert = $('#successAlert');
    const startBtn = $('#startBtn');
    
    // Initialize tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
    
    // Make provider cards clickable
    $('.provider-card').on('click', function(e) {
        // Don't toggle if clicking directly on the checkbox
        if (!$(e.target).is('input.provider-checkbox')) {
            const checkbox = $(this).find('input.provider-checkbox');
            checkbox.prop('checked', !checkbox.prop('checked'));
            updateProviderCardSelection();
        }
    });
    
    // Update card selection status when checkboxes change
    $('.provider-checkbox').on('change', function() {
        updateProviderCardSelection();
    });
    
    // Initialize card selection state
    updateProviderCardSelection();
    
    function updateProviderCardSelection() {
        $('.provider-card').each(function() {
            const checkbox = $(this).find('input.provider-checkbox');
            if (checkbox.prop('checked')) {
                $(this).addClass('selected');
            } else {
                $(this).removeClass('selected');
            }
        });
        
        // Update start button based on selection
        if ($('.provider-checkbox:checked').length > 0) {
            startBtn.prop('disabled', false);
        } else {
            startBtn.prop('disabled', true);
        }
    }
    
    // Check if a benchmark is already running on page load
    checkStatus();
    
    // Handle form submission
    $('#benchmarkForm').on('submit', function(e) {
        e.preventDefault();
        
        // Collect selected providers
        const selectedProviders = [];
        $('.provider-checkbox:checked').each(function() {
            selectedProviders.push($(this).val());
        });
        
        // Get number of runs from form
        const numRuns = parseInt($('#numRuns').val()) || 3;
        
        if (selectedProviders.length === 0) {
            showToast('Please select at least one cloud provider');
            return;
        }
        
        // Disable button and show spinner
        startBtn.prop('disabled', true);
        startBtn.html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Starting...');
        
        // Reset and show UI elements
        progressBar.css('width', '0%').attr('aria-valuenow', 0);
        progressText.text('Initializing... (0%)');
        progressDetails.text('Starting benchmark...');
        progressContainer.removeClass('d-none');
        runningAlert.removeClass('d-none alert-success alert-danger').addClass('alert-info')
            .html(`<h5><i class="bi bi-activity me-2"></i>Benchmark Running...</h5>
                  <p>Running benchmark for ${selectedProviders.length} provider(s) with ${numRuns} runs each.</p>`);
        successAlert.addClass('d-none');
        
        // Animate scroll to progress section
        $('html, body').animate({
            scrollTop: runningAlert.offset().top - 20
        }, 500);
        
        // Start the benchmark
        $.ajax({
            url: '/benchmark',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                providers: selectedProviders,
                num_runs: numRuns
            }),
            success: function(response) {
                console.log('Benchmark started:', response);
                // Start polling for status updates
                startPolling();
            },
            error: function(error) {
                console.error('Error starting benchmark:', error);
                showToast('Error starting benchmark: ' + (error.responseJSON ? error.responseJSON.message : 'Unknown error'));
                startBtn.prop('disabled', false);
                startBtn.html('<i class="bi bi-play-fill me-2"></i>Start Benchmark');
                runningAlert.removeClass('alert-info').addClass('alert-danger')
                    .html(`<h5><i class="bi bi-exclamation-triangle me-2"></i>Benchmark Error</h5>
                           <p>${error.responseJSON ? error.responseJSON.message : 'Unknown error occurred'}</p>`);
            }
        });
    });
    
    function showToast(message) {
        // Create a toast element if it doesn't exist
        if ($('#toast-container').length === 0) {
            $('body').append(`<div id="toast-container" class="position-fixed top-0 end-0 p-3" style="z-index: 1050"></div>`);
        }
        
        const toastId = 'toast-' + Date.now();
        const toast = `
            <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header">
                    <i class="bi bi-info-circle me-2 text-primary"></i>
                    <strong class="me-auto">CloudTrace</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;
        
        $('#toast-container').append(toast);
        const toastElement = new bootstrap.Toast(document.getElementById(toastId), {
            delay: 3000
        });
        toastElement.show();
    }
    
    // Functions for status checking and polling
    function checkStatus() {
        $.ajax({
            url: '/benchmark/status',
            type: 'GET',
            success: function(data) {
                console.log('Status check:', data);
                
                if (data.running) {
                    // Show running alert and progress
                    runningAlert.removeClass('d-none');
                    progressContainer.removeClass('d-none');
                    startBtn.prop('disabled', true);
                    
                    // Start polling for updates
                    startPolling();
                    
                    // Update UI with current progress
                    updateProgress(data.progress);
                }
            },
            error: function(error) {
                console.error('Error checking status:', error);
            }
        });
    }
    
    function startPolling() {
        // Clear existing interval if any
        if (pollingInterval) {
            clearInterval(pollingInterval);
        }
        
        // Poll every second
        pollingInterval = setInterval(pollStatus, 1000);
    }
    
    function pollStatus() {
        $.ajax({
            url: '/benchmark/status',
            type: 'GET',
            success: function(data) {
                console.log('Poll status:', data);
                
                if (data.running || (data.progress && data.progress.status === 'running')) {
                    // Update progress UI
                    updateProgress(data.progress);
                } else if (data.progress && data.progress.status === 'complete') {
                    // Show completion
                    if (data.progress.progress >= 100) {
                        showCompletion();
                    } else {
                        // Wait for one more poll if status is complete but progress < 100%
                        updateProgress(data.progress);
                    }
                } else if (data.progress && data.progress.status === 'error') {
                    // Show error
                    showError(data.progress.error || 'Unknown error occurred');
                } else if (!data.running && data.last_run) {
                    // Check if results exist
                    if (data.results_file_exists && data.results_file_size > 0) {
                        showCompletion();
                    } else {
                        showError('Benchmark completed but results may be missing');
                    }
                }
            },
            error: function(error) {
                console.error('Error polling status:', error);
            }
        });
    }
    
    function updateProgress(progress) {
        if (!progress) return;
        
        const percent = progress.progress || 0;
        
        // Update progress bar with smooth animation
        progressBar.css('width', percent + '%').attr('aria-valuenow', percent);
        
        // Update text based on status
        let statusText = '';
        let iconClass = 'bi-hourglass-split';
        
        if (progress.status === 'complete') {
            statusText = 'Complete (100%)';
            iconClass = 'bi-check-circle';
        } else if (percent < 5) {
            statusText = 'Initializing...';
            iconClass = 'bi-arrow-clockwise';
        } else {
            statusText = `${progress.current_provider || 'Processing'} (${Math.round(percent)}%)`;
            iconClass = 'bi-arrow-repeat';
        }
        
        // Update progress text with icon
        progressText.html(`<i class="bi ${iconClass} me-1"></i> ${statusText}`);
        
        // Update details
        let details = '';
        
        // Add details based on progress state
        if (progress.status === 'complete') {
            details = 'Benchmark complete! Results ready to view.';
        } else if (percent < 5) {
            details = 'Setting up benchmark environment...';
        } else if (progress.current_provider) {
            details = `Processing: ${progress.current_provider}`;
            if (progress.completed && progress.total) {
                details += ` (${progress.completed}/${progress.total})`;
            }
        }
        
        // Add elapsed time if available
        if (progress.start_time) {
            const elapsed = Math.round((Date.now() / 1000) - progress.start_time);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            details += ` • Time elapsed: ${minutes}m ${seconds.toString().padStart(2, '0')}s`;
        }
        
        progressDetails.text(details);
    }
    
    function showCompletion() {
        // Stop polling
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
        
        // Update UI
        progressBar.css('width', '100%').attr('aria-valuenow', 100)
                   .removeClass('progress-bar-animated');
        progressText.html('<i class="bi bi-check-circle-fill me-1"></i> Complete (100%)');
        
        // Show success message and results link
        runningAlert.removeClass('alert-info').addClass('alert-success')
            .html(`<h5><i class="bi bi-check-circle me-2"></i>Benchmark Complete!</h5>
                   <p>The benchmark has completed successfully.</p>
                   <a href="/visualize" class="btn btn-success">
                       <i class="bi bi-bar-chart me-2"></i>View Results
                   </a>`);
        
        // Show success alert as well
        successAlert.removeClass('d-none');
        
        // Re-enable button
        startBtn.prop('disabled', false);
        startBtn.html('<i class="bi bi-play-fill me-2"></i>Start Benchmark');
        
        // Show toast notification
        showToast('Benchmark completed successfully!');
        
        // Animate scroll to results section
        $('html, body').animate({
            scrollTop: runningAlert.offset().top - 20
        }, 500);
    }
    
    function showError(message) {
        // Stop polling
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
        
        // Update UI
        runningAlert.removeClass('alert-info').addClass('alert-danger')
            .html(`<h5><i class="bi bi-exclamation-triangle me-2"></i>Benchmark Error</h5>
                   <p>${message}</p>
                   <button class="btn btn-outline-danger" onclick="location.reload()">
                       <i class="bi bi-arrow-repeat me-2"></i>Try Again
                   </button>`);
        
        // Re-enable button
        startBtn.prop('disabled', false);
        startBtn.html('<i class="bi bi-play-fill me-2"></i>Start Benchmark');
        
        // Show toast notification
        showToast('Benchmark error: ' + message);
    }
});