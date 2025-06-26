/**
 * Admin Review Search - AJAX Implementation
 * Enhances the review management search with AJAX functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize review search if elements exist
    if (document.getElementById('review-search-form')) {
        const reviewSearch = new AdminSearch({
            formId: 'review-search-form',
            inputId: 'review-search-input',
            resultContainerId: 'review-table-container',
            countDisplayId: 'review-count-display',
            apiEndpoint: '/api/admin/reviews',
            searchParam: 'search',
            instantSearch: true,
            debounceTime: 400,
            renderResults: renderReviewResults
        });
    }
    
    /**
     * Renders review search results
     * @param {Object} data - Review data from API
     * @param {HTMLElement} container - Container to render results into
     */
    function renderReviewResults(data, container) {
        if (!data.reviews || data.reviews.length === 0) {
            container.innerHTML = `
                <div class="alert alert-info text-center" role="alert">
                    <i class="fas fa-info-circle me-2"></i>
                    No reviews found matching your search criteria.
                </div>
            `;
            return;
        }
        
        // Build HTML for review table
        let html = `
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>User</th>
                        <th>Car</th>
                        <th>Rating</th>
                        <th>Review</th>
                        <th>Status</th>
                        <th>Date</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        // Add rows for each review
        data.reviews.forEach(review => {
            // Generate star rating display
            const starRating = '★'.repeat(review.rating) + '☆'.repeat(5 - review.rating);
            
            // Determine status badge color
            let statusBadgeClass = 'secondary';
            if (review.is_approved) statusBadgeClass = 'success';
            else statusBadgeClass = 'warning';
            
            html += `
                <tr>
                    <td>${review.id}</td>
                    <td>
                        ${review.user ? `
                            <div>
                                <strong>${review.user.name}</strong><br>
                                <small>${review.user.email}</small>
                            </div>
                        ` : 'N/A'}
                    </td>
                    <td>
                        ${review.car ? `
                            <div>
                                <strong>${review.car.make} ${review.car.model}</strong><br>
                                <small>${review.car.year}</small>
                            </div>
                        ` : 'N/A'}
                    </td>
                    <td>
                        <span class="text-warning">${starRating}</span>
                        <small class="d-block">${review.rating}/5</small>
                    </td>
                    <td>
                        <div class="review-content" style="max-width: 250px; overflow: hidden; text-overflow: ellipsis;">
                            ${review.review_text}
                        </div>
                    </td>
                    <td>
                        <span class="badge bg-${statusBadgeClass}">
                            ${review.is_approved ? 'Approved' : 'Pending'}
                        </span>
                    </td>
                    <td>${review.created_at}</td>
                    <td>
                        <div class="btn-group">
                            ${!review.is_approved ? `
                                <form action="/admin/reviews/${review.id}/approve" method="POST" style="display: inline;">
                                    <button type="submit" class="btn btn-sm btn-outline-success">
                                        <i class="fas fa-check"></i>
                                    </button>
                                </form>
                            ` : `
                                <form action="/admin/reviews/${review.id}/disapprove" method="POST" style="display: inline;">
                                    <button type="submit" class="btn btn-sm btn-outline-warning">
                                        <i class="fas fa-times"></i>
                                    </button>
                                </form>
                            `}
                            <form action="/admin/reviews/${review.id}/delete" method="POST" style="display: inline;">
                                <button type="submit" class="btn btn-sm btn-outline-danger" onclick="return confirm('Are you sure you want to delete this review?');">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </form>
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