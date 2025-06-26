/**
 * Admin Payment List - AJAX Filtering
 * Enhances the payment management page with AJAX-based filtering
 */

// Global config object to store settings
let paymentFilterConfig = {
    formId: 'payment-filter-form',
    tableContainerId: 'payment-table-container',
    countDisplayId: 'payment-count-display',
    statsContainerId: 'payment-stats-container',
    activeFiltersContainerId: 'active-filters-container',
    apiEndpoint: '/api/admin/payments',
    pageUrl: '/admin/payments'
};

/**
 * Initialize the payment filters system
 * @param {Object} config - Configuration options
 */
function initPaymentFilters(config) {
    // Update global config
    paymentFilterConfig = { ...paymentFilterConfig, ...config };
    
    // Get form element
    const filterForm = document.getElementById(paymentFilterConfig.formId);
    
    if (filterForm) {
        // Prevent default form submission
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            applyFiltersAndSearch();
            return false;
        });
        
        // Add event listeners for immediate filter updates (dropdowns)
        const immediateFilterElements = filterForm.querySelectorAll('.immediate-filter');
        immediateFilterElements.forEach(element => {
            element.addEventListener('change', function() {
                applyFiltersAndSearch();
            });
        });
        
        // Add event listeners for text input filters (as you type with debounce)
        let debounceTimer;
        const textInputs = filterForm.querySelectorAll('input[type="text"]');
        textInputs.forEach(input => {
            // Keep the Enter key functionality for immediate search
            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    clearTimeout(debounceTimer);
                    applyFiltersAndSearch();
                }
            });
            
            // Add input event for search as you type
            input.addEventListener('input', function() {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    applyFiltersAndSearch();
                }, 500); // 500ms debounce time
            });
        });
        
        // Add event listeners for date inputs
        const dateInputs = filterForm.querySelectorAll('input[type="date"]');
        dateInputs.forEach(input => {
            input.addEventListener('change', function() {
                applyFiltersAndSearch();
            });
        });
        
        // Initialize active filters display
        updateActiveFiltersDisplay();
        
        // Add event listeners for individual filter clear buttons
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('clear-filter') || e.target.closest('.clear-filter')) {
                const filterElement = e.target.closest('.clear-filter');
                const filterName = filterElement.dataset.filter;
                
                // Clear this specific filter
                const inputElement = document.getElementById(filterName);
                if (inputElement) {
                    inputElement.value = '';
                    applyFiltersAndSearch();
                }
            }
        });
        
        // Initial load - if URL has parameters, apply them
        if (window.location.search) {
            setTimeout(() => {
                applyFiltersAndSearch();
            }, 100);
        }
    }
}

/**
 * Collects form data and builds URL parameters
 * @returns {URLSearchParams} The URL parameters for the filter query
 */
function collectFormData() {
    const filterForm = document.getElementById(paymentFilterConfig.formId);
    if (!filterForm) return new URLSearchParams();
    
    const formData = new FormData(filterForm);
    const params = new URLSearchParams();
    
    // Add non-empty values to params
    for (const [key, value] of formData.entries()) {
        if (value.trim() !== '') {
            params.append(key, value);
        }
    }
    
    return params;
}

/**
 * Applies filters and search criteria using AJAX
 */
function applyFiltersAndSearch() {
    const tableContainer = document.getElementById(paymentFilterConfig.tableContainerId);
    
    // Show loading state
    if (tableContainer) {
        tableContainer.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Loading payments...</p>
            </div>
        `;
    }
    
    // Get URL parameters
    const params = collectFormData();
    
    // Make AJAX request
    fetch(`${paymentFilterConfig.apiEndpoint}?${params.toString()}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Update the payment table with new data
            updatePaymentTable(data);
            
            // Update stats display
            updateStatsDisplay(data.stats);
            
            // Update active filters display
            updateActiveFiltersDisplay();
            
            // Update URL without page refresh
            const url = new URL(window.location);
            url.search = params.toString();
            window.history.pushState({}, '', url);
        })
        .catch(error => {
            console.error('Error fetching payments:', error);
            if (tableContainer) {
                tableContainer.innerHTML = `
                    <div class="alert alert-danger" role="alert">
                        <i class="fas fa-exclamation-circle me-2"></i>
                        Failed to load payments. Please try again.
                        <p class="mt-2">Error: ${error.message}</p>
                    </div>
                `;
            }
        });
}

/**
 * Updates payment statistics display
 * @param {Object} stats - The payment statistics
 */
function updateStatsDisplay(stats) {
    const statsContainer = document.getElementById(paymentFilterConfig.statsContainerId);
    if (!statsContainer) return;

    // Update total revenue
    const revenueElement = statsContainer.querySelector('.total-revenue');
    if (revenueElement) {
        revenueElement.textContent = `₱${stats.total_revenue.toFixed(2)}`;
    }

    // Update pending payments
    const pendingElement = statsContainer.querySelector('.total-pending');
    if (pendingElement) {
        pendingElement.textContent = `₱${stats.total_pending.toFixed(2)}`;
    }

    // Update total transactions
    const transactionsElement = statsContainer.querySelector('.total-transactions');
    if (transactionsElement) {
        transactionsElement.textContent = stats.total_payments;
    }
}

/**
 * Resets all filters and refreshes the payment list
 */
function resetAllFilters() {
    const filterForm = document.getElementById(paymentFilterConfig.formId);
    if (!filterForm) return;
    
    // Reset form fields
    filterForm.reset();
    
    // Clear URL parameters
    const url = new URL(window.location);
    url.search = '';
    window.history.pushState({}, '', url);
    
    // Reset active filters display
    const activeFiltersContainer = document.getElementById(paymentFilterConfig.activeFiltersContainerId);
    if (activeFiltersContainer) {
        activeFiltersContainer.innerHTML = '';
        activeFiltersContainer.classList.add('d-none');
    }
    
    // Reload payments without filters
    fetch(paymentFilterConfig.apiEndpoint)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            updatePaymentTable(data);
            updateStatsDisplay(data.stats);
        })
        .catch(error => {
            console.error('Error fetching payments during reset:', error);
            const tableContainer = document.getElementById(paymentFilterConfig.tableContainerId);
            if (tableContainer) {
                tableContainer.innerHTML = `
                    <div class="alert alert-danger" role="alert">
                        <i class="fas fa-exclamation-circle me-2"></i>
                        Failed to reset filters. Please try again or refresh the page.
                    </div>
                `;
            }
        });
}

/**
 * Updates the payment table with filtered data
 * @param {Object} data - The payment data from the API
 */
function updatePaymentTable(data) {
    const tableContainer = document.getElementById(paymentFilterConfig.tableContainerId);
    if (!tableContainer) return;
    
    // Update payment count display
    const countDisplay = document.getElementById(paymentFilterConfig.countDisplayId);
    if (countDisplay) {
        countDisplay.textContent = `${data.count} Results`;
    }
    
    // If no payments found
    if (!data.payments || data.payments.length === 0) {
        tableContainer.innerHTML = `
            <div class="alert alert-info text-center py-4">
                <i class="fas fa-info-circle me-2"></i>
                No payment records found matching your filters.
            </div>
        `;
        return;
    }
    
    // Build HTML for payment table
    let html = `
    <div class="table-responsive">
        <table class="table table-hover mb-0">
            <thead class="table-light">
                <tr>
                    <th>ID</th>
                    <th>Date</th>
                    <th>User</th>
                    <th>Booking Ref</th>
                    <th>Amount</th>
                    <th>Method</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    // Add rows for each payment
    data.payments.forEach(payment => {
        // Format user info
        const userName = payment.user ? payment.user.name : 'N/A';
        const userId = payment.user ? payment.user.id : '';
        const userLink = userId ? `<a href="/admin/users/${userId}">${userName}</a>` : userName;
        
        // Format booking info
        const bookingRef = payment.booking ? payment.booking.reference : 'N/A';
        
        // Determine payment method display
        const paymentMethod = payment.payment_method ? 
            payment.payment_method.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase()) : 
            'N/A';
        
        // Determine payment type badge
        const typeClass = payment.is_late_fee ? 'bg-danger' : 'bg-info';
        const typeText = payment.is_late_fee ? 'Late Fee' : 'Booking';
        
        // Determine status badge
        let statusClass = 'bg-secondary';
        if (payment.status === 'completed') statusClass = 'bg-success';
        else if (payment.status === 'pending') statusClass = 'bg-warning';
        else if (payment.status === 'failed') statusClass = 'bg-danger';
        else if (payment.status === 'refunded') statusClass = 'bg-secondary';
        
        // Format actions dropdown
        let actionsDropdown = `
            <div class="dropdown">
                <button class="btn btn-sm btn-outline-secondary dropdown-toggle" type="button" id="action-${payment.id}" data-bs-toggle="dropdown" aria-expanded="false">
                    Actions
                </button>
                <ul class="dropdown-menu" aria-labelledby="action-${payment.id}">
        `;
        
        // Add conditional actions based on payment status
        if (payment.status === 'pending') {
            actionsDropdown += `
                <li>
                    <form action="/admin/payments/${payment.id}/complete" method="POST" style="display: inline;">
                        <button type="submit" class="dropdown-item">
                            <i class="fas fa-check me-2"></i> Mark as Completed
                        </button>
                    </form>
                </li>
            `;
        }
        
        if (payment.status !== 'refunded' && payment.status === 'completed') {
            actionsDropdown += `
                <li>
                    <form action="/admin/payments/${payment.id}/refund" method="POST" style="display: inline;">
                        <button type="submit" class="dropdown-item" onclick="return confirm('Are you sure you want to refund this payment? This action cannot be undone.');">
                            <i class="fas fa-undo me-2"></i> Refund Payment
                        </button>
                    </form>
                </li>
            `;
        }
        
        // Add view details action
        actionsDropdown += `
            <li>
                <a class="dropdown-item" href="/admin/payments/${payment.id}">
                    <i class="fas fa-file-invoice me-2"></i> View Details
                </a>
            </li>
        `;
        
        // Add view booking action if available
        if (payment.booking) {
            actionsDropdown += `
                <li>
                    <a class="dropdown-item" href="/admin/bookings/${payment.booking.id}">
                        <i class="fas fa-calendar-alt me-2"></i> View Booking
                    </a>
                </li>
            `;
        }
        
        // Close dropdown
        actionsDropdown += `
                </ul>
            </div>
        `;
        
        // Add row to table
        html += `
            <tr>
                <td>${payment.id}</td>
                <td>${payment.payment_date}</td>
                <td>${userLink}</td>
                <td>${bookingRef}</td>
                <td class="${payment.is_late_fee ? 'text-danger' : ''}">₱${payment.amount.toFixed(2)}</td>
                <td>${paymentMethod}</td>
                <td><span class="badge ${typeClass}">${typeText}</span></td>
                <td><span class="badge ${statusClass}">${payment.status.charAt(0).toUpperCase() + payment.status.slice(1)}</span></td>
                <td>${actionsDropdown}</td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
    </div>
    `;
    
    tableContainer.innerHTML = html;
}

/**
 * Updates the active filters section based on current filter values
 */
function updateActiveFiltersDisplay() {
    const activeFiltersContainer = document.getElementById(paymentFilterConfig.activeFiltersContainerId);
    if (!activeFiltersContainer) return;
    
    const params = collectFormData();
    
    if (params.toString() === '') {
        activeFiltersContainer.innerHTML = '';
        activeFiltersContainer.classList.add('d-none');
        return;
    }
    
    let html = '<h6>Active Filters:</h6><div>';
    let hasFilters = false;
    
    // Add badges for each active filter
    if (params.has('type') && params.get('type').trim() !== '') {
        const typeText = params.get('type') === 'booking' ? 'Booking Payments' : 'Late Fees';
        html += `<span class="badge bg-primary me-2">Type: ${typeText} <i class="fas fa-times ms-1 clear-filter" data-filter="type"></i></span>`;
        hasFilters = true;
    }
    
    if (params.has('status') && params.get('status').trim() !== '') {
        html += `<span class="badge bg-primary me-2">Status: ${params.get('status').charAt(0).toUpperCase() + params.get('status').slice(1)} <i class="fas fa-times ms-1 clear-filter" data-filter="status"></i></span>`;
        hasFilters = true;
    }
    
    if (params.has('start_date') && params.get('start_date').trim() !== '') {
        html += `<span class="badge bg-primary me-2">From: ${params.get('start_date')} <i class="fas fa-times ms-1 clear-filter" data-filter="start_date"></i></span>`;
        hasFilters = true;
    }
    
    if (params.has('end_date') && params.get('end_date').trim() !== '') {
        html += `<span class="badge bg-primary me-2">To: ${params.get('end_date')} <i class="fas fa-times ms-1 clear-filter" data-filter="end_date"></i></span>`;
        hasFilters = true;
    }
    
    if (params.has('search') && params.get('search').trim() !== '') {
        html += `<span class="badge bg-primary me-2">Search: ${params.get('search')} <i class="fas fa-times ms-1 clear-filter" data-filter="search"></i></span>`;
        hasFilters = true;
    }
    
    html += '</div>';
    
    if (hasFilters) {
        activeFiltersContainer.innerHTML = html;
        activeFiltersContainer.classList.remove('d-none');
    } else {
        activeFiltersContainer.innerHTML = '';
        activeFiltersContainer.classList.add('d-none');
    }
}

/**
 * Checks if any filters are currently applied
 * @returns {boolean} True if filters are applied, false otherwise
 */
function isFiltered() {
    const filterForm = document.getElementById(paymentFilterConfig.formId);
    if (!filterForm) return false;
    
    const formData = new FormData(filterForm);
    for (const [_, value] of formData.entries()) {
        if (value.trim() !== '') return true;
    }
    
    return false;
} 