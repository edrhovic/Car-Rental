/**
 * Admin User Search - AJAX Implementation
 * Enhances the user management search with AJAX functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize user search if elements exist
    if (document.getElementById('user-search-form')) {
        const userSearch = new AdminSearch({
            formId: 'user-search-form',
            inputId: 'user-search-input',
            resultContainerId: 'user-table-container',
            countDisplayId: 'user-count-display',
            apiEndpoint: '/api/admin/users',
            searchParam: 'search',
            instantSearch: true,
            debounceTime: 400,
            renderResults: renderUserResults
        });
    }
    
    /**
     * Renders user search results
     * @param {Object} data - User data from API
     * @param {HTMLElement} container - Container to render results into
     */
    function renderUserResults(data, container) {
        if (!data.users || data.users.length === 0) {
            container.innerHTML = `
                <div class="alert alert-info text-center" role="alert">
                    <i class="fas fa-info-circle me-2"></i>
                    No users found matching your search criteria.
                </div>
            `;
            return;
        }
        
        // Build HTML for user table
        let html = `
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Status</th>
                        <th>Registration Date</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        // Add rows for each user
        data.users.forEach(user => {
            html += `
                <tr>
                    <td>${user.id}</td>
                    <td>
                        <div class="d-flex align-items-center">
                            <div class="avatar-icon me-2">
                                <i class="fas fa-user-circle fa-2x text-secondary"></i>
                            </div>
                            <div>
                                <strong>${user.first_name} ${user.last_name}</strong><br>
                                <small>${user.username}</small>
                            </div>
                        </div>
                    </td>
                    <td>${user.email}</td>
                    <td>
                        <span class="badge bg-${user.is_admin ? 'primary' : 'secondary'}">
                            ${user.is_admin ? 'Admin' : 'User'}
                        </span>
                    </td>
                    <td>
                        <span class="badge bg-${user.is_active ? 'success' : 'danger'}">
                            ${user.is_active ? 'Active' : 'Inactive'}
                        </span>
                    </td>
                    <td>${user.registration_date}</td>
                    <td>
                        <div class="btn-group">
                            <a href="/admin/users/${user.id}" class="btn btn-sm btn-outline-primary">
                                <i class="fas fa-eye"></i>
                            </a>
                            <a href="/admin/users/${user.id}/edit" class="btn btn-sm btn-outline-secondary">
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
        
        container.innerHTML = html;
    }
}); 