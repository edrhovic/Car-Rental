/**
 * Admin Car List - AJAX Filtering and Searching
 * Enhances the car management page with AJAX-based filtering and searching
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get form and container elements
    const filterForm = document.getElementById('admin-car-filter-form');
    const carTableContainer = document.getElementById('car-table-container');
    const carCountDisplay = document.getElementById('car-count-display');
    const filterStats = document.getElementById('filter-stats');
    const activeFiltersContainer = document.getElementById('active-filters-container');
    
    if (filterForm) {
        // Prevent default form submission
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            applyFiltersAndSearch();
        });
        
        // Add event listeners for immediate filter updates
        const immediateFilterElements = filterForm.querySelectorAll('.immediate-filter');
        immediateFilterElements.forEach(element => {
            element.addEventListener('change', function() {
                applyFiltersAndSearch();
            });
        });
        
        // Add search as you type with debounce for text inputs
        let debounceTimer;
        const searchInput = filterForm.querySelector('input[name="search"]');
        if (searchInput) {
            // Keep the Enter key functionality for immediate search
            searchInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    clearTimeout(debounceTimer);
                    applyFiltersAndSearch();
                }
            });
            
            // Add input event for search as you type
            searchInput.addEventListener('input', function() {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    applyFiltersAndSearch();
                }, 500); // 500ms debounce time
            });
        }
        
        // Add clear filters functionality
        const clearFiltersButtons = document.querySelectorAll('.clear-filters-btn');
        clearFiltersButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                resetFilters();
            });
        });
    }
    
    /**
     * Collects form data and builds URL parameters
     * @returns {URLSearchParams} The URL parameters for the filter query
     */
    function collectFormData() {
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
        // Show loading state
        if (carTableContainer) {
            carTableContainer.innerHTML = `
                <div class="text-center py-5">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">Loading cars...</p>
                </div>
            `;
        }
        
        // Get URL parameters
        const params = collectFormData();
        
        // Make AJAX request
        fetch(`/api/admin/cars?${params.toString()}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Update the car table with new data
                updateCarTable(data);
                
                // Update active filters display
                updateActiveFilters(params);
                
                // Update URL without page refresh
                const url = new URL(window.location);
                url.search = '';
                url.search = params.toString();
                window.history.pushState({}, '', url);
            })
            .catch(error => {
                console.error('Error fetching cars:', error);
                if (carTableContainer) {
                    carTableContainer.innerHTML = `
                        <div class="alert alert-danger" role="alert">
                            <i class="fas fa-exclamation-circle me-2"></i>
                            Failed to load cars. Please try again.
                            <p class="mt-2">Error: ${error.message}</p>
                        </div>
                    `;
                }
            });
    }
    
    /**
     * Resets all filters and refreshes the car list
     */
    function resetFilters() {
        try {
            // Reset form fields
            filterForm.reset();
            
            // Clear URL parameters
            const url = new URL(window.location);
            url.search = '';
            window.history.pushState({}, '', url);
            
            // Reset active filters display
            if (activeFiltersContainer) {
                activeFiltersContainer.innerHTML = '';
                activeFiltersContainer.classList.add('d-none');
            }
            
            // Reload cars without filters - use direct request
            fetch('/api/admin/cars')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    updateCarTable(data);
                })
                .catch(error => {
                    console.error('Error fetching cars during reset:', error);
                    if (carTableContainer) {
                        carTableContainer.innerHTML = `
                            <div class="alert alert-danger" role="alert">
                                <i class="fas fa-exclamation-circle me-2"></i>
                                Failed to reset filters. Please try again or refresh the page.
                            </div>
                        `;
                    }
                });
        } catch (error) {
            console.error('Error in resetFilters function:', error);
        }
    }
    
    /**
     * Updates the car table with filtered data
     * @param {Object} data - The car data from the API
     */
    function updateCarTable(data) {
        if (!carTableContainer) return;
        
        // Update car count display
        if (carCountDisplay) {
            if (data.count === 1) {
                carCountDisplay.textContent = '1 car found';
            } else {
                carCountDisplay.textContent = `${data.count} cars found`;
            }
        }
        
        // Update filter stats display
        if (filterStats) {
            if (isFiltered()) {
                filterStats.textContent = `Filtered Cars (${data.count})`;
            } else {
                filterStats.textContent = `All Cars (${data.count})`;
            }
        }
        
        // If no cars found
        if (!data.cars || data.cars.length === 0) {
            carTableContainer.innerHTML = `
                <div class="alert alert-info text-center" role="alert">
                    <i class="fas fa-info-circle me-2"></i>
                    No cars found with the selected filters.
                </div>
            `;
            return;
        }
        
        // Build HTML for car table
        let html = `
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Make & Model</th>
                        <th>Year</th>
                        <th>License Plate</th>
                        <th>Status</th>
                        <th>Rate/Day</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        // Add rows for each car
        data.cars.forEach(car => {
            html += `
                <tr>
                    <td>${car.id}</td>
                    <td>
                        <div class="d-flex align-items-center">
                            <div class="car-thumbnail me-2">
                                ${car.image_url ? 
                                    `<img src="${car.image_url}" alt="${car.make} ${car.model}" width="50">` : 
                                    `<div class="placeholder-thumbnail"><i class="fas fa-car"></i></div>`
                                }
                            </div>
                            <div>
                                <strong>${car.make} ${car.model}</strong><br>
                                <small class="text-muted">${car.transmission}</small>
                            </div>
                        </div>
                    </td>
                    <td>${car.year}</td>
                    <td>${car.license_plate}</td>
                    <td>
<<<<<<< HEAD
                        ${car.is_available ? 
                            `<span class="badge bg-success">Available</span>` : 
                            `<span class="badge bg-danger">Rented</span>`
=======
                        ${car.status === 'available' ?
                            `<span class="badge bg-success">Available</span>` :
                            car.status === 'rented' ?
                            `<span class="badge bg-warning">Rented</span>` :
                            car.status === 'maintenance' ?
                            `<span class="badge bg-secondary">In Maintenance</span>` :
                            `<span class="badge bg-info">Offered for Loan</span>`
>>>>>>> 8a8ec6c (fixed some bugs on status, modified the api, fixed some routings, and some logics)
                        }
                    </td>
                    <td>₱${car.daily_rate}</td>
                    <td>
                        <div class="btn-group">
                            <a href="/admin/cars/${car.id}" class="btn btn-sm btn-outline-primary">
                                <i class="fas fa-eye"></i>
                            </a>
                            <a href="/admin/cars/${car.id}/edit" class="btn btn-sm btn-outline-secondary">
                                <i class="fas fa-edit"></i>
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
        
        carTableContainer.innerHTML = html;
    }
    
    /**
     * Updates the active filters section based on current filter values
     * @param {URLSearchParams} params - The current URL parameters
     */
    function updateActiveFilters(params) {
        if (!activeFiltersContainer) return;
        
        if (params.toString() === '') {
            activeFiltersContainer.innerHTML = '';
            activeFiltersContainer.classList.add('d-none');
            return;
        }
        
        let html = '<h6>Active Filters:</h6><div>';
        let hasFilters = false;
        
        // Add badges for each active filter
        if (params.has('search') && params.get('search').trim() !== '') {
            html += `<span class="badge bg-primary me-2">Search: ${params.get('search')}</span>`;
            hasFilters = true;
        }
        
        if (params.has('make') && params.get('make').trim() !== '') {
            html += `<span class="badge bg-primary me-2">Make: ${params.get('make')}</span>`;
            hasFilters = true;
        }
        
        if (params.has('model') && params.get('model').trim() !== '') {
            html += `<span class="badge bg-primary me-2">Model: ${params.get('model')}</span>`;
            hasFilters = true;
        }
        
        if (params.has('year') && params.get('year').trim() !== '') {
            html += `<span class="badge bg-primary me-2">Year: ${params.get('year')}</span>`;
            hasFilters = true;
        }
        
        if (params.has('availability') && params.get('availability').trim() !== '') {
            const availText = params.get('availability') === 'available' ? 'Available' : 'Rented';
            html += `<span class="badge bg-primary me-2">Status: ${availText}</span>`;
            hasFilters = true;
        }
        
        if (params.has('transmission') && params.get('transmission').trim() !== '') {
            html += `<span class="badge bg-primary me-2">Transmission: ${params.get('transmission')}</span>`;
            hasFilters = true;
        }
        
        if (params.has('fuel_type') && params.get('fuel_type').trim() !== '') {
            html += `<span class="badge bg-primary me-2">Fuel Type: ${params.get('fuel_type')}</span>`;
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
        if (!filterForm) return false;
        
        const formData = new FormData(filterForm);
        for (const [_, value] of formData.entries()) {
            if (value.trim() !== '') return true;
        }
        
        return false;
    }
    
    // Initial load - if URL has parameters, apply them
    if (window.location.search && filterForm) {
        // Wait a moment for form to initialize
        setTimeout(() => {
            applyFiltersAndSearch();
        }, 100);
    }
}); 