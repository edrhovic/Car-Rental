/**
 * Late Fees Functionality
 * Handles late fees data loading and display
 */

document.addEventListener('DOMContentLoaded', function() {
    // Update late fees badge in navbar
    updateLateFeeBadge();
    
    // Update profile late fees section
    updateProfileLateFees();
});

/**
 * Updates the late fees badge in the navigation bar
 */
function updateLateFeeBadge() {
    const lateFeeBadge = document.getElementById('late-fees-badge');
    if (lateFeeBadge) {
        // Fetch late fees data
        fetchLateFeesSummary()
            .then(data => {
                // Update the badge with the count
                if (data.count > 0) {
                    lateFeeBadge.textContent = data.count;
                    lateFeeBadge.classList.remove('d-none');
                } else {
                    lateFeeBadge.classList.add('d-none');
                }
            })
            .catch(error => {
                console.error('Error updating late fees badge:', error);
                lateFeeBadge.classList.add('d-none');
            });
    }
}

/**
 * Updates the late fees section on the profile page
 */
function updateProfileLateFees() {
    // Only run this code if the late fees section exists
    const lateFeeSection = document.getElementById('late-fees-section');
    if (lateFeeSection) {
        // Fetch late fees data
        fetchLateFeesSummary()
            .then(data => {
                // Update the section with the fetched data
                if (data.count > 0) {
                    let html = `
                        <div class="alert alert-warning mb-2">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            You have <strong>${data.count}</strong> outstanding late ${data.count === 1 ? 'fee' : 'fees'} 
                            totaling <strong>$${data.total_amount.toFixed(2)}</strong>
                        </div>
                        <p class="text-danger mb-0"><small>Late fees must be paid to maintain account privileges.</small></p>
                    `;
                    lateFeeSection.innerHTML = html;
                } else {
                    let html = `
                        <div class="alert alert-success mb-0">
                            <i class="fas fa-check-circle me-2"></i>
                            You have no outstanding late fees.
                        </div>
                    `;
                    lateFeeSection.innerHTML = html;
                }
            })
            .catch(error => {
                console.error('Error fetching late fees:', error);
                lateFeeSection.innerHTML = `
                    <div class="alert alert-danger mb-0">
                        <i class="fas fa-exclamation-circle me-2"></i>
                        Unable to load late fees information.
                    </div>
                `;
            });
    }
}

/**
 * Fetches the late fees summary data from the API
 * @returns {Promise} Promise with the late fees data
 */
function fetchLateFeesSummary() {
    return fetch('/api/user/late-fees-summary')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        });
} 