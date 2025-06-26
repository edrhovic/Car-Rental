/**
 * Admin Booking List - AJAX Filtering
 * Enhances the bookings management page with AJAX-based filtering
 */

// Global config object to store settings
let bookingFilterConfig = {
    formId: 'admin-booking-filter-form',
    tableContainerId: 'booking-table-container',
    countDisplayId: 'booking-count-display',
    filterStatsId: 'filter-stats',
    activeFiltersContainerId: 'active-filters-container',
    apiEndpoint: '/api/admin/bookings',
    pageUrl: '/admin/bookings'
};

/**
 * Initialize the booking filters system
 * @param {Object} config - Configuration options
 */
function initBookingFilters(config) {
    // Update global config
    bookingFilterConfig = { ...bookingFilterConfig, ...config };
    
    // Get form element
    const filterForm = document.getElementById(bookingFilterConfig.formId);
    
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
    const filterForm = document.getElementById(bookingFilterConfig.formId);
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
    const tableContainer = document.getElementById(bookingFilterConfig.tableContainerId);
    
    // Show loading state
    if (tableContainer) {
        tableContainer.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Loading bookings...</p>
            </div>
        `;
    }
    
    // Get URL parameters
    const params = collectFormData();
    
    // Make AJAX request
    fetch(`${bookingFilterConfig.apiEndpoint}?${params.toString()}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Update the booking table with new data
            updateBookingTable(data);
            
            // Update active filters display
            updateActiveFiltersDisplay();
            
            // Update URL without page refresh
            const url = new URL(window.location);
            url.search = params.toString();
            window.history.pushState({}, '', url);
        })
        .catch(error => {
            console.error('Error fetching bookings:', error);
            if (tableContainer) {
                tableContainer.innerHTML = `
                    <div class="alert alert-danger" role="alert">
                        <i class="fas fa-exclamation-circle me-2"></i>
                        Failed to load bookings. Please try again.
                        <p class="mt-2">Error: ${error.message}</p>
                    </div>
                `;
            }
        });
}

/**
 * Resets all filters and refreshes the booking list
 */
function resetAllFilters() {
    const filterForm = document.getElementById(bookingFilterConfig.formId);
    if (!filterForm) return;
    
    // Reset form fields
    filterForm.reset();
    
    // Clear URL parameters
    const url = new URL(window.location);
    url.search = '';
    window.history.pushState({}, '', url);
    
    // Reset active filters display
    const activeFiltersContainer = document.getElementById(bookingFilterConfig.activeFiltersContainerId);
    if (activeFiltersContainer) {
        activeFiltersContainer.innerHTML = '';
        activeFiltersContainer.classList.add('d-none');
    }
    
    // Reload bookings without filters
    fetch(bookingFilterConfig.apiEndpoint)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            updateBookingTable(data);
        })
        .catch(error => {
            console.error('Error fetching bookings during reset:', error);
            const tableContainer = document.getElementById(bookingFilterConfig.tableContainerId);
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
 * Updates the booking table with filtered data
 * @param {Object} data - The booking data from the API
 */
function updateBookingTable(data) {
    const tableContainer = document.getElementById(bookingFilterConfig.tableContainerId);
    if (!tableContainer) return;
    
    // Update booking count display
    const countDisplay = document.getElementById(bookingFilterConfig.countDisplayId);
    if (countDisplay) {
        if (data.count === 1) {
            countDisplay.textContent = '1 booking found';
        } else {
            countDisplay.textContent = `${data.count} bookings found`;
        }
    }
    
    // Update filter stats display
    const filterStats = document.getElementById(bookingFilterConfig.filterStatsId);
    if (filterStats) {
        if (isFiltered()) {
            filterStats.textContent = `Filtered Bookings (${data.count})`;
        } else {
            filterStats.textContent = `All Bookings (${data.count})`;
        }
    }
    
    // If no bookings found
    if (!data.bookings || data.bookings.length === 0) {
        tableContainer.innerHTML = `
            <div class="alert alert-info text-center" role="alert">
                <i class="fas fa-info-circle me-2"></i>
                No bookings found with the selected filters.
            </div>
        `;
        return;
    }
    
    // Build HTML for booking table
    let html = `
    <div class="table-responsive">
        <table class="table table-striped table-hover">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>User ID</th>
                    <th>User</th>
                    <th>Car</th>
                    <th>Pickup Date</th>
                    <th>Return Date</th>
                    <th>Location</th>
                    <th>Total Price</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    // Add rows for each booking
    data.bookings.forEach(booking => {
        // Format car info
        const carInfo = booking.car ? `${booking.car.year} ${booking.car.make} ${booking.car.model}` : 'No car selected';
        
        // Determine status badge class
        let statusBadgeClass = 'bg-secondary';
        if (booking.status === 'pending') statusBadgeClass = 'bg-warning';
        else if (booking.status === 'confirmed') statusBadgeClass = 'bg-primary';
        else if (booking.status === 'completed') statusBadgeClass = 'bg-success';
        else if (booking.status === 'cancelled') statusBadgeClass = 'bg-danger';
        
        // Format booking ID to BKNG-XXX format
        const formattedId = booking.booking_reference || `BKNG-${String(booking.id).padStart(3, '0')}`;
        
        html += `
            <tr>
                <td>${formattedId}</td>
                <td>${booking.user.id}</td>
                <td>
                    <a href="/admin/users/${booking.user.id}">
                        ${booking.user.email}
                    </a>
                </td>
                <td>${carInfo}</td>
                <td>${booking.start_date}</td>
                <td>${booking.end_date}</td>
                <td>
                    <small class="d-block">
                        <i class="fas fa-map-marker-alt me-1"></i> 
                        ${booking.pickup_location && booking.pickup_location !== 'Branch Not Recorded' 
                            ? booking.pickup_location 
                            : '<span class="text-muted">Branch Not Recorded</span>'}
                    </small>
                </td>
                <td>₱${booking.total_cost}</td>
                <td>
                    <span class="badge ${statusBadgeClass}">
                        ${booking.status.charAt(0).toUpperCase() + booking.status.slice(1)}
                    </span>
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <a href="/admin/bookings/${booking.id}" class="btn btn-outline-primary">
                            <i class="fas fa-eye"></i>
                        </a>
                    </div>
                </td>
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
    const activeFiltersContainer = document.getElementById(bookingFilterConfig.activeFiltersContainerId);
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
    if (params.has('booking_id') && params.get('booking_id').trim() !== '') {
        html += `<span class="badge bg-primary me-2">Booking ID: ${params.get('booking_id')} <i class="fas fa-times ms-1 clear-filter" data-filter="booking_id"></i></span>`;
        hasFilters = true;
    }
    
    if (params.has('user_id') && params.get('user_id').trim() !== '') {
        html += `<span class="badge bg-primary me-2">User ID: ${params.get('user_id')} <i class="fas fa-times ms-1 clear-filter" data-filter="user_id"></i></span>`;
        hasFilters = true;
    }
    
    if (params.has('status') && params.get('status').trim() !== '') {
        html += `<span class="badge bg-primary me-2">Status: ${params.get('status')} <i class="fas fa-times ms-1 clear-filter" data-filter="status"></i></span>`;
        hasFilters = true;
    }
    
    if (params.has('date_range') && params.get('date_range').trim() !== '') {
        const dateRangeText = params.get('date_range') === 'today' ? 'Today' : 
                             params.get('date_range') === 'week' ? 'This Week' : 
                             'This Month';
        html += `<span class="badge bg-primary me-2">Date Range: ${dateRangeText} <i class="fas fa-times ms-1 clear-filter" data-filter="date_range"></i></span>`;
        hasFilters = true;
    }
    
    if (params.has('location') && params.get('location').trim() !== '') {
        html += `<span class="badge bg-primary me-2">Location: ${params.get('location')} <i class="fas fa-times ms-1 clear-filter" data-filter="location"></i></span>`;
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
    const filterForm = document.getElementById(bookingFilterConfig.formId);
    if (!filterForm) return false;
    
    const formData = new FormData(filterForm);
    for (const [_, value] of formData.entries()) {
        if (value.trim() !== '') return true;
    }
    
    return false;
} 