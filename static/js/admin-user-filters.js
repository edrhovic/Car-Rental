/**
 * Admin User List - AJAX Filtering
 * Enhances the user management page with AJAX-based filtering
 */

// Global config object to store settings
let userFilterConfig = {
    formId: 'filterForm',
    tableContainerId: 'user-table-container',
    countDisplayId: 'user-count-display',
    filterStatsId: 'filter-stats',
    activeFiltersContainerId: 'active-filters-container',
    apiEndpoint: '/api/admin/users',
    pageUrl: '/admin/users'
};

/**
 * Initialize the user filters system
 * @param {Object} config - Configuration options
 */
function initUserFilters(config) {
    // Update global config
    userFilterConfig = { ...userFilterConfig, ...config };
    
    // Get form element
    const filterForm = document.getElementById(userFilterConfig.formId);
    
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
    const filterForm = document.getElementById(userFilterConfig.formId);
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
    const tableContainer = document.getElementById(userFilterConfig.tableContainerId);
    
    // Show loading state
    if (tableContainer) {
        tableContainer.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Loading users...</p>
            </div>
        `;
    }
    
    // Get URL parameters
    const params = collectFormData();
    
    // Make AJAX request
    fetch(`${userFilterConfig.apiEndpoint}?${params.toString()}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Update the user table with new data
            updateUserTable(data);
            
            // Update active filters display
            updateActiveFiltersDisplay();
            
            // Update URL without page refresh
            const url = new URL(window.location);
            url.search = params.toString();
            window.history.pushState({}, '', url);
        })
        .catch(error => {
            console.error('Error fetching users:', error);
            if (tableContainer) {
                tableContainer.innerHTML = `
                    <div class="alert alert-danger" role="alert">
                        <i class="fas fa-exclamation-circle me-2"></i>
                        Failed to load users. Please try again.
                        <p class="mt-2">Error: ${error.message}</p>
                    </div>
                `;
            }
        });
}

/**
 * Resets all filters and refreshes the user list
 */
function resetAllFilters() {
    const filterForm = document.getElementById(userFilterConfig.formId);
    if (!filterForm) return;
    
    // Reset form fields
    filterForm.reset();
    
    // Clear URL parameters
    const url = new URL(window.location);
    url.search = '';
    window.history.pushState({}, '', url);
    
    // Reset active filters display
    const activeFiltersContainer = document.getElementById(userFilterConfig.activeFiltersContainerId);
    if (activeFiltersContainer) {
        activeFiltersContainer.innerHTML = '';
        activeFiltersContainer.classList.add('d-none');
    }
    
    // Reload users without filters
    fetch(userFilterConfig.apiEndpoint)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            updateUserTable(data);
        })
        .catch(error => {
            console.error('Error fetching users during reset:', error);
            const tableContainer = document.getElementById(userFilterConfig.tableContainerId);
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
 * Updates the user table with filtered data
 * @param {Object} data - The user data from the API
 */
function updateUserTable(data) {
    const tableContainer = document.getElementById(userFilterConfig.tableContainerId);
    if (!tableContainer) return;
    
    // Update user count display
    const countDisplay = document.getElementById(userFilterConfig.countDisplayId);
    if (countDisplay) {
        if (data.count === 1) {
            countDisplay.textContent = '1 user found';
        } else {
            countDisplay.textContent = `${data.count} users found`;
        }
    }
    
    // Update filter stats display
    const filterStats = document.getElementById(userFilterConfig.filterStatsId);
    if (filterStats) {
        if (isFiltered()) {
            filterStats.textContent = `Filtered Users (${data.count})`;
        } else {
            filterStats.textContent = `All Users (${data.count})`;
        }
    }
    
    // If no users found
    if (!data.users || data.users.length === 0) {
        tableContainer.innerHTML = `
            <div class="alert alert-info text-center" role="alert">
                <i class="fas fa-info-circle me-2"></i>
                No users found with the selected filters.
            </div>
        `;
        return;
    }
    
    // Build HTML for user table
    let html = `
    <div class="table-responsive">
        <table class="table table-striped table-hover align-middle">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>Role</th>
                    <th>Join Date</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    // Add rows for each user
    data.users.forEach(user => {
        // Get initials for avatar
        const firstInitial = user.first_name ? user.first_name[0] : '';
        const lastInitial = user.last_name ? user.last_name[0] : '';
        const initials = (firstInitial + lastInitial).toUpperCase();
        
        // Determine role badge class
        const roleBadgeClass = user.is_admin ? 'bg-danger' : 'bg-info';
        const roleBadgeText = user.is_admin ? 'Admin' : 'User';
        
        // Determine status badge class
        const statusBadgeClass = user.is_active ? 'bg-success' : 'bg-warning';
        const statusBadgeText = user.is_active ? 'Active' : 'Inactive';
        
        html += `
            <tr>
                <td>${user.id}</td>
                <td>
                    <div class="d-flex align-items-center">
                        <div class="avatar me-2">
                            <div class="avatar-initial rounded-circle bg-secondary">
                                ${initials}
                            </div>
                        </div>
                        <div>${user.full_name}</div>
                    </div>
                </td>
                <td>${user.email}</td>
                <td>${user.phone_number}</td>
                <td>
                    <span class="badge ${roleBadgeClass}">
                        ${roleBadgeText}
                    </span>
                </td>
                <td>${user.registration_date}</td>
                <td>
                    <span class="badge ${statusBadgeClass}">
                        ${statusBadgeText}
                    </span>
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <a href="/admin/users/${user.id}/edit" class="btn btn-outline-primary">
                            <i class="fas fa-edit"></i>
                        </a>
                        <a href="/admin/users/${user.id}" class="btn btn-outline-secondary">
                            <i class="fas fa-eye"></i>
                        </a>
                        ${!user.is_admin ? `
                        <button type="button" class="btn btn-outline-danger" onclick="confirmDelete(${user.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                        ` : ''}
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
    const activeFiltersContainer = document.getElementById(userFilterConfig.activeFiltersContainerId);
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
    if (params.has('search') && params.get('search').trim() !== '') {
        html += `<span class="badge bg-primary me-2">Search: ${params.get('search')} <i class="fas fa-times ms-1 clear-filter" data-filter="search"></i></span>`;
        hasFilters = true;
    }
    
    if (params.has('role') && params.get('role').trim() !== '') {
        const roleText = params.get('role') === 'admin' ? 'Admin' : 'User';
        html += `<span class="badge bg-primary me-2">Role: ${roleText} <i class="fas fa-times ms-1 clear-filter" data-filter="role"></i></span>`;
        hasFilters = true;
    }
    
    if (params.has('status') && params.get('status').trim() !== '') {
        const statusText = params.get('status') === 'active' ? 'Active' : 'Inactive';
        html += `<span class="badge bg-primary me-2">Status: ${statusText} <i class="fas fa-times ms-1 clear-filter" data-filter="status"></i></span>`;
        hasFilters = true;
    }
    
    if (params.has('sort') && params.get('sort').trim() !== '') {
        let sortText = '';
        switch (params.get('sort')) {
            case 'id_asc': sortText = 'ID (Oldest First)'; break;
            case 'id_desc': sortText = 'ID (Newest First)'; break;
            case 'name_asc': sortText = 'Name (A-Z)'; break;
            case 'name_desc': sortText = 'Name (Z-A)'; break;
            case 'email_asc': sortText = 'Email (A-Z)'; break;
            case 'email_desc': sortText = 'Email (Z-A)'; break;
            case 'date_asc': sortText = 'Join Date (Oldest)'; break;
            case 'date_desc': sortText = 'Join Date (Newest)'; break;
            default: sortText = params.get('sort');
        }
        html += `<span class="badge bg-primary me-2">Sort: ${sortText} <i class="fas fa-times ms-1 clear-filter" data-filter="sort"></i></span>`;
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
    const filterForm = document.getElementById(userFilterConfig.formId);
    if (!filterForm) return false;
    
    const formData = new FormData(filterForm);
    for (const [key, value] of formData.entries()) {
        if (value.trim() !== '' && key !== 'sort') return true;
    }
    
    return false;
} 