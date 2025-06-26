/**
 * Car Search & Filter AJAX Handler
 * Manages AJAX requests for filtering and searching cars
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get the filter form and car listings container
    const filterForm = document.getElementById('car-filter-form');
    const carListingsContainer = document.getElementById('car-listings-container');
    const totalCarsCount = document.getElementById('total-cars-count');
    
    if (filterForm) {
        // Prevent default form submission and use AJAX instead
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            applyFiltersAndSearch();
        });
        
        // Add event listeners to filter elements that should trigger immediate update
        const immediateFilterElements = filterForm.querySelectorAll('.immediate-filter');
        immediateFilterElements.forEach(element => {
            element.addEventListener('change', function() {
                applyFiltersAndSearch();
            });
        });
        
        // Add event listener for search button
        const searchBtn = document.getElementById('search-btn');
        if (searchBtn) {
            searchBtn.addEventListener('click', function() {
                applyFiltersAndSearch();
            });
        }
        
        // Add event listener for search field to allow searching as you type
        const searchField = document.getElementById('search');
        if (searchField) {
            let typingTimer;
            const doneTypingInterval = 500; // wait for 500ms after user stops typing
            
            searchField.addEventListener('keyup', function() {
                clearTimeout(typingTimer);
                typingTimer = setTimeout(applyFiltersAndSearch, doneTypingInterval);
            });
            
            searchField.addEventListener('keydown', function() {
                clearTimeout(typingTimer);
            });
        }
        
        // Add event listener for reset filters button
        const resetFiltersBtn = document.getElementById('reset-filters-btn');
        if (resetFiltersBtn) {
            resetFiltersBtn.addEventListener('click', function(e) {
                e.preventDefault();
                resetFilters();
            });
        }
    }
    
    /**
     * Applies filters and search using AJAX
     */
    function applyFiltersAndSearch() {
        // Show loading state
        const loadingIndicator = document.getElementById('loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.classList.remove('d-none');
        }
        
        if (carListingsContainer) {
            carListingsContainer.classList.add('d-none');
        }
        
        // Get form data as URL parameters
        const formData = new FormData(filterForm);
        const urlParams = new URLSearchParams();
        
        // Only add non-empty values to URL parameters
        for (const [key, value] of formData.entries()) {
            if (value.trim() !== '') {
                urlParams.append(key, value);
            }
        }
        
        // Make AJAX request
        fetch(`/api/cars?${urlParams.toString()}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Update UI with the results
                updateCarListings(data);
                
                // Hide loading indicator
                if (loadingIndicator) {
                    loadingIndicator.classList.add('d-none');
                }
                
                if (carListingsContainer) {
                    carListingsContainer.classList.remove('d-none');
                }
                
                // Update URL to reflect current filters without page refresh
                const url = new URL(window.location);
                
                // Clear all existing parameters first
                url.search = '';
                
                // Add only non-empty parameters
                for (const [key, value] of formData.entries()) {
                    if (value.trim() !== '') {
                        url.searchParams.set(key, value);
                    }
                }
                
                window.history.pushState({}, '', url);
            })
            .catch(error => {
                console.error('Error fetching cars:', error);
                // Hide loading indicator
                if (loadingIndicator) {
                    loadingIndicator.classList.add('d-none');
                }
                
                if (carListingsContainer) {
                    carListingsContainer.classList.remove('d-none');
                    carListingsContainer.innerHTML = `
                        <div class="alert alert-danger text-center" role="alert">
                            <i class="fas fa-exclamation-circle me-2"></i>
                            Failed to load cars. Please try again.
                            <p class="mt-2">Error: ${error.message}</p>
                        </div>
                    `;
                }
            });
    }
    
    /**
     * Resets all filters and refreshes the car listings
     */
    function resetFilters() {
        try {
            // Reset all form fields
            filterForm.reset();
            
            // Clear URL parameters
            const url = new URL(window.location);
            url.search = '';
            window.history.pushState({}, '', url);
            
            // Reload cars without filters - use direct request
            fetch('/api/cars')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    updateCarListings(data);
                })
                .catch(error => {
                    console.error('Error fetching cars during reset:', error);
                    if (carListingsContainer) {
                        carListingsContainer.innerHTML = `
                            <div class="alert alert-danger text-center" role="alert">
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
     * Updates the car listings in the UI
     * @param {Object} data - The car data from the API
     */
    function updateCarListings(data) {
        if (!carListingsContainer) return;
        
        // Update total cars count
        if (totalCarsCount) {
            totalCarsCount.textContent = `${data.count} car(s) found`;
        }
        
        // If no cars found
        if (!data.cars || data.cars.length === 0) {
            carListingsContainer.innerHTML = `
                <div class="card">
                    <div class="card-body text-center py-5">
                        <i class="fas fa-car fa-3x mb-3 text-muted"></i>
                        <h4>No cars found</h4>
                        <p class="mb-0">Try adjusting your filters or search term.</p>
                        <button id="empty-reset-btn" class="btn btn-outline-primary mt-3">Reset Filters</button>
                    </div>
                </div>
            `;
            
            // Add event listener to the reset button
            const emptyResetBtn = document.getElementById('empty-reset-btn');
            if (emptyResetBtn) {
                emptyResetBtn.addEventListener('click', resetFilters);
            }
            
            return;
        }
        
        // Build HTML for car listings
        let html = '<div class="row">';
        
        data.cars.forEach(car => {
            html += `
                <div class="col-md-6 col-lg-4 mb-4">
                    <div class="card car-card h-100">
                        <div class="position-relative">
                            ${car.image_url ? 
                                `<img src="${car.image_url}" class="card-img-top" alt="${car.make} ${car.model}">` : 
                                `<img src="/static/images/car-placeholder.jpg" class="card-img-top" alt="Car Placeholder">`
                            }
                            
                            ${car.average_rating && car.average_rating > 0 ? 
                                `<span class="badge bg-warning position-absolute top-0 end-0 m-2">
                                    <i class="fas fa-star me-1"></i>${typeof car.average_rating === 'number' ? car.average_rating.toFixed(1) : car.average_rating}
                                </span>` : ''
                            }
                        </div>
                        <div class="card-body">
                            <h5 class="card-title">${car.year} ${car.make} ${car.model}</h5>
                            <ul class="car-specs">
                                <li><i class="fas fa-cog me-2"></i> ${car.transmission}</li>
                                <li><i class="fas fa-gas-pump me-2"></i> ${car.fuel_type}</li>
                                <li><i class="fas fa-users me-2"></i> ${car.seats} seats</li>
                            </ul>
                            <p class="car-price">₱${car.daily_rate} / day</p>
                        </div>
                        <div class="card-footer">
                            <div class="d-grid gap-2">
                                <a href="/cars/${car.id}" class="btn btn-primary">View Details</a>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        carListingsContainer.innerHTML = html;
    }
    
    // Initial load - if URL has parameters, apply them
    if (window.location.search) {
        // Wait a moment for form to initialize
        setTimeout(() => {
            applyFiltersAndSearch();
        }, 100);
    }
}); 