document.addEventListener('DOMContentLoaded', function() {
    const benchmarkForm = document.getElementById('benchmark-form');
    const runButton = document.getElementById('runButton');
    const spinner = document.getElementById('spinner');
    const runningAlert = document.getElementById('runningAlert');
    const successAlert = document.getElementById('successAlert');
    
    benchmarkForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get selected providers
        const selectedProviders = Array.from(
            document.querySelectorAll('input[type="checkbox"]:checked')
        ).map(cb => cb.value);
        
        if (selectedProviders.length === 0) {
            alert('Please select at least one cloud provider.');
            return;
        }
        
        // Disable form and show loading indicators
        runButton.disabled = true;
        spinner.classList.remove('d-none');
        runningAlert.classList.remove('d-none');
        successAlert.classList.add('d-none');
        
        // Run benchmark API call
        fetch('/benchmark', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                providers: selectedProviders
            }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Show success message and enable the form again
            runningAlert.classList.add('d-none');
            successAlert.classList.remove('d-none');
            runButton.disabled = false;
            spinner.classList.add('d-none');
        })
        .catch(error => {
            console.error('Error:', error);
            runningAlert.classList.add('d-none');
            runButton.disabled = false;
            spinner.classList.add('d-none');
            
            // Show error message
            const errorAlert = document.createElement('div');
            errorAlert.className = 'alert alert-danger mt-4';
            errorAlert.innerHTML = '<strong>Error:</strong> Failed to run benchmark. Please try again.';
            benchmarkForm.after(errorAlert);
            
            // Remove error message after 5 seconds
            setTimeout(() => {
                errorAlert.remove();
            }, 5000);
        });
    });
});