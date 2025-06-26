/**
 * AdminSearch - Core AJAX Search Utility
 * Reusable class for implementing AJAX search functionality across the admin panel
 */

class AdminSearch {
    /**
     * Initialize a new AdminSearch instance
     * @param {Object} config - Configuration options
     * @param {string} config.formId - ID of the search form element
     * @param {string} config.inputId - ID of the search input element
     * @param {string} config.resultContainerId - ID of the container to display results
     * @param {string} config.countDisplayId - ID of element to display result count (optional)
     * @param {string} config.apiEndpoint - API endpoint URL to fetch search results
     * @param {string} config.searchParam - Name of the search parameter (default: 'search')
     * @param {boolean} config.instantSearch - Whether to search as you type (default: true)
     * @param {number} config.debounceTime - Debounce time in milliseconds (default: 300)
     * @param {Function} config.renderResults - Function to render results
     */
    constructor(config) {
        this.formId = config.formId;
        this.inputId = config.inputId;
        this.resultContainerId = config.resultContainerId;
        this.countDisplayId = config.countDisplayId;
        this.apiEndpoint = config.apiEndpoint;
        this.searchParam = config.searchParam || 'search';
        this.instantSearch = config.instantSearch !== undefined ? config.instantSearch : true;
        this.debounceTime = config.debounceTime || 300;
        this.renderResults = config.renderResults;
        
        this.form = document.getElementById(this.formId);
        this.input = document.getElementById(this.inputId);
        this.resultsContainer = document.getElementById(this.resultContainerId);
        this.countDisplay = this.countDisplayId ? document.getElementById(this.countDisplayId) : null;
        
        this.debounceTimer = null;
        
        this.init();
    }
    
    /**
     * Initialize event listeners
     */
    init() {
        if (!this.form || !this.input || !this.resultsContainer) {
            console.error('AdminSearch: Required elements not found');
            return;
        }
        
        // Handle form submission
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.performSearch();
        });
        
        // Handle instant search (search as you type)
        if (this.instantSearch && this.input) {
            this.input.addEventListener('input', () => {
                this.debounceSearch();
            });
        }
        
        // Initial search if there's a value
        if (this.input.value.trim()) {
            this.performSearch();
        }
    }
    
    /**
     * Debounce search to prevent too many requests
     */
    debounceSearch() {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            this.performSearch();
        }, this.debounceTime);
    }
    
    /**
     * Perform the search request
     */
    performSearch() {
        const searchTerm = this.input.value.trim();
        const url = new URL(this.apiEndpoint, window.location.origin);
        
        // Add search parameter
        if (searchTerm) {
            url.searchParams.append(this.searchParam, searchTerm);
        }
        
        // Add any additional form data
        const formData = new FormData(this.form);
        for (const [key, value] of formData.entries()) {
            if (key !== this.searchParam && value) {
                url.searchParams.append(key, value);
            }
        }
        
        this.showLoading();
        
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                this.hideLoading();
                this.renderResults(data, this.resultsContainer);
                this.updateCountDisplay(data);
            })
            .catch(error => {
                this.hideLoading();
                this.showError(error);
                console.error('Search error:', error);
            });
    }
    
    /**
     * Show loading indicator
     */
    showLoading() {
        // Add loading class to container
        this.resultsContainer.classList.add('loading');
        
        // Add loading spinner if not already present
        if (!this.resultsContainer.querySelector('.search-loading')) {
            const loadingHtml = `
                <div class="search-loading text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">Searching...</p>
                </div>
            `;
            this.resultsContainer.innerHTML = loadingHtml;
        }
    }
    
    /**
     * Hide loading indicator
     */
    hideLoading() {
        this.resultsContainer.classList.remove('loading');
    }
    
    /**
     * Show error message
     * @param {Error} error - The error object
     */
    showError(error) {
        this.resultsContainer.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Error: ${error.message || 'An error occurred while searching'}
            </div>
        `;
    }
    
    /**
     * Update the count display if it exists
     * @param {Object} data - The response data
     */
    updateCountDisplay(data) {
        if (!this.countDisplay) return;
        
        let count = 0;
        
        // Try to determine count from data
        if (data.count !== undefined) {
            count = data.count;
        } else {
            // Check common data structures
            const dataArrays = ['users', 'cars', 'bookings', 'payments', 'reviews'];
            for (const key of dataArrays) {
                if (data[key] && Array.isArray(data[key])) {
                    count = data[key].length;
                    break;
                }
            }
        }
        
        // Update display
        this.countDisplay.textContent = `${count} results found`;
    }
} 