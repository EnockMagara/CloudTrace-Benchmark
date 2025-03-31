$(document).ready(function() {
    let pollingInterval;
    const progressBar = $('#progressBar');
    const progressText = $('#progressText');
    const progressDetails = $('#progressDetails');
    const progressContainer = $('#progressContainer');
    const runningAlert = $('#runningAlert');
    const successAlert = $('#successAlert');
    const startBtn = $('#startBtn');
    
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
            alert('Please select at least one cloud provider');
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
            .html(`<h5>Benchmark Running...</h5>
                  <p>Running benchmark for ${selectedProviders.length} provider(s) with ${numRuns} runs each.</p>`);
        successAlert.addClass('d-none');
        
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
                alert('Error starting benchmark: ' + (error.responseJSON ? error.responseJSON.message : 'Unknown error'));
                startBtn.prop('disabled', false);
                startBtn.html('Start Benchmark');
                runningAlert.removeClass('alert-info').addClass('alert-danger')
                    .html(`<h5>Benchmark Error</h5>
                           <p>${error.responseJSON ? error.responseJSON.message : 'Unknown error occurred'}</p>`);
            }
        });
    });
    
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
        
        // Update progress bar
        progressBar.css('width', percent + '%').attr('aria-valuenow', percent);
        
        // Update text based on status
        let statusText = '';
        if (progress.status === 'complete') {
            statusText = 'Complete (100%)';
        } else if (percent < 5) {
            statusText = 'Initializing...';
        } else {
            statusText = `${progress.current_provider || 'Processing'} (${Math.round(percent)}%)`;
        }
        
        // Update progress text
        progressText.text(statusText);
        
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
            details += ` • Time elapsed: ${minutes}m ${seconds}s`;
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
        progressBar.css('width', '100%').attr('aria-valuenow', 100);
        progressText.text('Complete (100%)');
        
        // Show success message and results link
        runningAlert.removeClass('alert-info').addClass('alert-success')
            .html(`<h5>Benchmark Complete!</h5>
                   <p>The benchmark has completed successfully.</p>
                   <a href="/visualize" class="btn btn-primary">View Results</a>`);
        
        // Show success alert as well
        successAlert.removeClass('d-none');
        
        // Re-enable button
        startBtn.prop('disabled', false);
        startBtn.html('Start Benchmark');
    }
    
    function showError(message) {
        // Stop polling
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
        
        // Update UI
        runningAlert.removeClass('alert-info').addClass('alert-danger')
            .html(`<h5>Benchmark Error</h5>
                   <p>${message}</p>`);
        
        // Re-enable button
        startBtn.prop('disabled', false);
        startBtn.html('Start Benchmark');
    }
});