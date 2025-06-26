/**
 * Customer Car Search - AJAX Implementation
 * Enhances the customer car search with AJAX functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize car search if elements exist
    if (document.getElementById('car-search-form')) {
        const carSearch = new AdminSearch({
            formId: 'car-search-form',
            inputId: 'car-search-input',
            resultContainerId: 'car-results-container',
            countDisplayId: 'car-count-display',
            apiEndpoint: '/api/cars',
            searchParam: 'search',
            instantSearch: true,
            debounceTime: 400,
            renderResults: renderCarResults
        });
        
        // Add additional filter handling
        const filterElements = document.querySelectorAll('.car-filter');
        if (filterElements.length > 0) {
            filterElements.forEach(filter => {
                filter.addEventListener('change', function() {
                    document.getElementById('car-search-form').dispatchEvent(new Event('submit'));
                });
            });
        }
    }
    
    /**
     * Renders car search results
     * @param {Object} data - Car data from API
     * @param {HTMLElement} container - Container to render results into
     */
    function renderCarResults(data, container) {
        if (!data.cars || data.cars.length === 0) {
            container.innerHTML = `
                <div class="alert alert-info text-center py-5" role="alert">
                    <i class="fas fa-info-circle fa-3x mb-3"></i>
                    <h4>No cars found</h4>
                    <p class="mb-0">Try adjusting your filters or search term.</p>
                </div>
            `;
            return;
        }
        
        // Update car count if element exists
        const countEl = document.getElementById('car-count-display');
        if (countEl) {
            countEl.textContent = `${data.cars.length} cars found`;
        }
        
        // Build HTML for car grid
        let html = '<div class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">';
        
        // Add card for each car
        data.cars.forEach(car => {
            html += `
                <div class="col">
                    <div class="card h-100 car-card">
                        <div class="position-relative">
                            ${car.image_url ? 
                                `<img src="${car.image_url}" class="card-img-top" alt="${car.make} ${car.model}" style="height: 200px; object-fit: cover;">` : 
                                `<div class="card-img-top d-flex align-items-center justify-content-center bg-light" style="height: 200px;">
                                    <i class="fas fa-car fa-3x text-secondary"></i>
                                </div>`
                            }
                            <div class="position-absolute top-0 end-0 p-2">
                                <span class="badge bg-success">Available</span>
                            </div>
                        </div>
                        <div class="card-body">
                            <h5 class="card-title">${car.make} ${car.model} (${car.year})</h5>
                            <div class="mb-2">
                                <span class="text-warning">
                                    ${car.avg_rating ? '★'.repeat(Math.round(car.avg_rating)) + '☆'.repeat(5 - Math.round(car.avg_rating)) : '☆☆☆☆☆'}
                                </span>
                                <small class="text-muted">${car.review_count || 0} reviews</small>
                            </div>
                            <div class="car-features mb-3">
                                <span class="badge bg-light text-dark me-1"><i class="fas fa-cog me-1"></i>${car.transmission}</span>
                                <span class="badge bg-light text-dark me-1"><i class="fas fa-gas-pump me-1"></i>${car.fuel_type}</span>
                                <span class="badge bg-light text-dark me-1"><i class="fas fa-user me-1"></i>${car.seats} seats</span>
                            </div>
                            <p class="card-text">${car.description ? car.description.substring(0, 100) + '...' : 'No description available.'}</p>
                        </div>
                        <div class="card-footer d-flex justify-content-between align-items-center">
                            <h5 class="mb-0 text-primary">₱${car.daily_rate}/day</h5>
                            <a href="/cars/${car.id}" class="btn btn-primary">View Details</a>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        
        container.innerHTML = html;
    }
}); 