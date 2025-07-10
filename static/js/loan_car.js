// Global variables to store original data
let originalOfferedCars = [];
let originalAvailableCars = [];

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeFilters();
    populateFilterOptions();
    
    // Store original data for filtering
    storeOriginalData();
    
    // Set up tab change handlers
    setupTabHandlers();
});

// Store original data for filtering
function storeOriginalData() {
    // Store offered cars
    originalOfferedCars = Array.from(document.querySelectorAll('.offered-car-item')).map(item => ({
        element: item,
        make: item.dataset.make || '',
        model: item.dataset.model || '',
        year: parseInt(item.dataset.year) || 0,
        status: item.dataset.status || '',
        price: parseFloat(item.dataset.price) || 0,
        date: item.dataset.date || '',
        search: item.dataset.search || ''
    }));
    
    // Store available cars
    originalAvailableCars = Array.from(document.querySelectorAll('.available-car-item')).map(item => ({
        element: item,
        make: item.dataset.make || '',
        model: item.dataset.model || '',
        year: parseInt(item.dataset.year) || 0,
        rate: parseFloat(item.dataset.rate) || 0,
        color: item.dataset.color || '',
        search: item.dataset.search || ''
    }));
}

// Initialize filter functionality
function initializeFilters() {
    // Add event listeners for search inputs
    const offeredSearch = document.getElementById('offered-search');
    const availableSearch = document.getElementById('available-search');
    
    if (offeredSearch) {
        offeredSearch.addEventListener('input', debounce(filterOfferedCars, 300));
    }
    
    if (availableSearch) {
        availableSearch.addEventListener('input', debounce(filterAvailableCars, 300));
    }
}

// Debounce function for search inputs
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Populate filter dropdown options
function populateFilterOptions() {
    populateOfferedFilterOptions();
    populateAvailableFilterOptions();
}

// Populate offered cars filter options
function populateOfferedFilterOptions() {
    const makeSelect = document.getElementById('offered-make');
    if (!makeSelect) return;
    
    const makes = new Set();
    originalOfferedCars.forEach(car => {
        if (car.make) makes.add(car.make);
    });
    
    // Clear existing options (keep "All Makes")
    const allMakesOption = makeSelect.querySelector('option[value=""]');
    makeSelect.innerHTML = '';
    if (allMakesOption) makeSelect.appendChild(allMakesOption);
    
    // Add sorted make options
    Array.from(makes).sort().forEach(make => {
        const option = document.createElement('option');
        option.value = make;
        option.textContent = capitalizeWords(make);
        makeSelect.appendChild(option);
    });
}

// Populate available cars filter options
function populateAvailableFilterOptions() {
    const makeSelect = document.getElementById('available-make');
    const colorSelect = document.getElementById('available-color');
    
    if (makeSelect) {
        const makes = new Set();
        originalAvailableCars.forEach(car => {
            if (car.make) makes.add(car.make);
        });
        
        // Clear existing options (keep "All Makes")
        const allMakesOption = makeSelect.querySelector('option[value=""]');
        makeSelect.innerHTML = '';
        if (allMakesOption) makeSelect.appendChild(allMakesOption);
        
        // Add sorted make options
        Array.from(makes).sort().forEach(make => {
            const option = document.createElement('option');
            option.value = make;
            option.textContent = capitalizeWords(make);
            makeSelect.appendChild(option);
        });
    }
    
    if (colorSelect) {
        const colors = new Set();
        originalAvailableCars.forEach(car => {
            if (car.color) colors.add(car.color);
        });
        
        // Clear existing options (keep "All Colors")
        const allColorsOption = colorSelect.querySelector('option[value=""]');
        colorSelect.innerHTML = '';
        if (allColorsOption) colorSelect.appendChild(allColorsOption);
        
        // Add sorted color options
        Array.from(colors).sort().forEach(color => {
            const option = document.createElement('option');
            option.value = color;
            option.textContent = capitalizeWords(color);
            colorSelect.appendChild(option);
        });
    }
}

// Capitalize words helper function
function capitalizeWords(str) {
    return str.split(' ').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
    ).join(' ');
}

// Filter offered cars
function filterOfferedCars() {
    const searchTerm = document.getElementById('offered-search')?.value.toLowerCase() || '';
    const statusFilter = document.getElementById('offered-status')?.value || '';
    const makeFilter = document.getElementById('offered-make')?.value || '';
    const yearFilter = document.getElementById('offered-year')?.value || '';
    const priceFilter = document.getElementById('offered-price')?.value || '';
    
    let filteredCars = originalOfferedCars.filter(car => {
        // Search filter
        if (searchTerm && !car.search.includes(searchTerm)) {
            return false;
        }
        
        // Status filter
        if (statusFilter && car.status !== statusFilter) {
            return false;
        }
        
        // Make filter
        if (makeFilter && car.make !== makeFilter) {
            return false;
        }
        
        // Year filter
        if (yearFilter && !filterByYearRange(car.year, yearFilter)) {
            return false;
        }
        
        // Price filter
        if (priceFilter && !filterByPriceRange(car.price, priceFilter)) {
            return false;
        }
        
        return true;
    });
    
    displayFilteredOfferedCars(filteredCars);
    updateOfferedCount(filteredCars.length);
}

// Filter available cars
function filterAvailableCars() {
    const searchTerm = document.getElementById('available-search')?.value.toLowerCase() || '';
    const makeFilter = document.getElementById('available-make')?.value || '';
    const yearFilter = document.getElementById('available-year')?.value || '';
    const rateFilter = document.getElementById('available-rate')?.value || '';
    const colorFilter = document.getElementById('available-color')?.value || '';
    
    let filteredCars = originalAvailableCars.filter(car => {
        // Search filter
        if (searchTerm && !car.search.includes(searchTerm)) {
            return false;
        }
        
        // Make filter
        if (makeFilter && car.make !== makeFilter) {
            return false;
        }
        
        // Year filter
        if (yearFilter && !filterByYearRange(car.year, yearFilter)) {
            return false;
        }
        
        // Rate filter
        if (rateFilter && !filterByRateRange(car.rate, rateFilter)) {
            return false;
        }
        
        // Color filter
        if (colorFilter && car.color !== colorFilter) {
            return false;
        }
        
        return true;
    });
    
    displayFilteredAvailableCars(filteredCars);
    updateAvailableCount(filteredCars.length);
}

// Year range filter helper
function filterByYearRange(year, range) {
    if (!range) return true;
    
    const [minYear, maxYear] = range.split('-').map(Number);
    return year >= minYear && year <= maxYear;
}

// Price range filter helper
function filterByPriceRange(price, range) {
    if (!range) return true;
    
    const [minPrice, maxPrice] = range.split('-').map(Number);
    return price >= minPrice && price <= maxPrice;
}

// Rate range filter helper
function filterByRateRange(rate, range) {
    if (!range) return true;
    
    const [minRate, maxRate] = range.split('-').map(Number);
    return rate >= minRate && rate <= maxRate;
}

// Display filtered offered cars
function displayFilteredOfferedCars(filteredCars) {
    const container = document.getElementById('offered-cars-container');
    const noResultsDiv = document.getElementById('offered-no-results');
    const emptyStateDiv = document.getElementById('offered-empty-state');
    
    if (!container) return;
    
    // Hide all car items first
    originalOfferedCars.forEach(car => {
        car.element.style.display = 'none';
    });
    
    if (filteredCars.length === 0) {
        // Show no results message
        if (noResultsDiv) {
            noResultsDiv.classList.remove('d-none');
        }
        if (emptyStateDiv) {
            emptyStateDiv.style.display = 'none';
        }
    } else {
        // Show filtered cars
        if (noResultsDiv) {
            noResultsDiv.classList.add('d-none');
        }
        if (emptyStateDiv) {
            emptyStateDiv.style.display = 'none';
        }
        
        filteredCars.forEach(car => {
            car.element.style.display = 'block';
        });
    }
}

// Display filtered available cars
function displayFilteredAvailableCars(filteredCars) {
    const container = document.getElementById('available-cars-container');
    const noResultsDiv = document.getElementById('available-no-results');
    const emptyStateDiv = document.getElementById('available-empty-state');
    
    if (!container) return;
    
    // Hide all car items first
    originalAvailableCars.forEach(car => {
        car.element.style.display = 'none';
    });
    
    if (filteredCars.length === 0) {
        // Show no results message
        if (noResultsDiv) {
            noResultsDiv.classList.remove('d-none');
        }
        if (emptyStateDiv) {
            emptyStateDiv.style.display = 'none';
        }
    } else {
        // Show filtered cars
        if (noResultsDiv) {
            noResultsDiv.classList.add('d-none');
        }
        if (emptyStateDiv) {
            emptyStateDiv.style.display = 'none';
        }
        
        filteredCars.forEach(car => {
            car.element.style.display = 'block';
        });
    }
}

// Update offered cars count
function updateOfferedCount(count) {
    const showingElement = document.getElementById('offered-showing');
    const countBadge = document.getElementById('offered-count');
    
    if (showingElement) {
        showingElement.textContent = count;
    }
    if (countBadge) {
        countBadge.textContent = count;
    }
}

// Update available cars count
function updateAvailableCount(count) {
    const showingElement = document.getElementById('available-showing');
    const countBadge = document.getElementById('available-count');
    
    if (showingElement) {
        showingElement.textContent = count;
    }
    if (countBadge) {
        countBadge.textContent = count;
    }
}

// Sort offered cars
function sortOfferedCars() {
    const sortBy = document.getElementById('offered-sort')?.value || 'newest';
    
    // Get currently filtered cars
    const visibleCars = originalOfferedCars.filter(car => 
        car.element.style.display !== 'none'
    );
    
    // Sort the visible cars
    visibleCars.sort((a, b) => {
        switch (sortBy) {
            case 'newest':
                return new Date(b.date) - new Date(a.date);
            case 'oldest':
                return new Date(a.date) - new Date(b.date);
            case 'price-low':
                return a.price - b.price;
            case 'price-high':
                return b.price - a.price;
            case 'year-new':
                return b.year - a.year;
            case 'year-old':
                return a.year - b.year;
            case 'make':
                return a.make.localeCompare(b.make);
            default:
                return 0;
        }
    });
    
    // Re-append elements in sorted order
    const container = document.getElementById('offered-cars-container');
    if (container) {
        visibleCars.forEach(car => {
            container.appendChild(car.element);
        });
    }
}

// Sort available cars
function sortAvailableCars() {
    const sortBy = document.getElementById('available-sort')?.value || 'make';
    
    // Get currently filtered cars
    const visibleCars = originalAvailableCars.filter(car => 
        car.element.style.display !== 'none'
    );
    
    // Sort the visible cars
    visibleCars.sort((a, b) => {
        switch (sortBy) {
            case 'make':
                return a.make.localeCompare(b.make);
            case 'rate-low':
                return a.rate - b.rate;
            case 'rate-high':
                return b.rate - a.rate;
            case 'year-new':
                return b.year - a.year;
            case 'year-old':
                return a.year - b.year;
            default:
                return 0;
        }
    });
    
    // Re-append elements in sorted order
    const container = document.getElementById('available-cars-container');
    if (container) {
        visibleCars.forEach(car => {
            container.appendChild(car.element);
        });
    }
}

// Clear offered cars filters
function clearOfferedFilters() {
    document.getElementById('offered-search').value = '';
    document.getElementById('offered-status').value = '';
    document.getElementById('offered-make').value = '';
    document.getElementById('offered-year').value = '';
    document.getElementById('offered-price').value = '';
    document.getElementById('offered-sort').value = 'newest';
    
    // Reset display
    originalOfferedCars.forEach(car => {
        car.element.style.display = 'block';
    });
    
    // Hide no results message
    const noResultsDiv = document.getElementById('offered-no-results');
    if (noResultsDiv) {
        noResultsDiv.classList.add('d-none');
    }
    
    // Update count
    updateOfferedCount(originalOfferedCars.length);
    
    // Re-sort
    sortOfferedCars();
}

// Clear available cars filters
function clearAvailableFilters() {
    document.getElementById('available-search').value = '';
    document.getElementById('available-make').value = '';
    document.getElementById('available-year').value = '';
    document.getElementById('available-rate').value = '';
    document.getElementById('available-color').value = '';
    document.getElementById('available-sort').value = 'make';
    
    // Reset display
    originalAvailableCars.forEach(car => {
        car.element.style.display = 'block';
    });
    
    // Hide no results message
    const noResultsDiv = document.getElementById('available-no-results');
    if (noResultsDiv) {
        noResultsDiv.classList.add('d-none');
    }
    
    // Update count
    updateAvailableCount(originalAvailableCars.length);
    
    // Re-sort
    sortAvailableCars();
}

// Setup tab handlers
function setupTabHandlers() {
    const offeredTab = document.getElementById('offered-tab');
    const availableTab = document.getElementById('available-tab');
    
    if (offeredTab) {
        offeredTab.addEventListener('shown.bs.tab', function() {
            // Refresh offered cars filters when tab is shown
            setTimeout(() => {
                filterOfferedCars();
            }, 100);
        });
    }
    
    if (availableTab) {
        availableTab.addEventListener('shown.bs.tab', function() {
            // Refresh available cars filters when tab is shown
            setTimeout(() => {
                filterAvailableCars();
            }, 100);
        });
    }
}

// Modal functions for car operations
function offerCarForLoan(carId, carDisplayName) {
    document.getElementById('car_id').value = carId;
    document.getElementById('selected_car_display').value = carDisplayName;
    
    const modal = new bootstrap.Modal(document.getElementById('offerCarModal'));
    modal.show();
}

function confirmWithdraw(loanCarId) {
    const modal = new bootstrap.Modal(document.getElementById('confirmWithdrawModal'));
    
    document.getElementById('confirmWithdrawBtn').onclick = function() {
        withdrawLoanCar(loanCarId);
        modal.hide();
    };
    
    modal.show();
}

function withdrawLoanCar(loanCarId) {
    fetch(`/admin/withdraw-loan-car/${loanCarId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => {
        if (response.ok) {
            location.reload();
        } else {
            console.error('Failed to withdraw loan car');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Helper function to get CSRF token if needed
function getCsrfToken() {
    const token = document.querySelector('meta[name="csrf-token"]');
    return token ? token.getAttribute('content') : '';
}

// Initialize filters on page load
document.addEventListener('DOMContentLoaded', function() {
    // Apply initial filters
    filterOfferedCars();
    filterAvailableCars();
    
    // Apply initial sorting
    sortOfferedCars();
    sortAvailableCars();
});