/**
 * Admin Booking Search - AJAX Implementation
 * Enhances the booking management search with AJAX functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize booking search if elements exist
    if (document.getElementById('booking-search-form')) {
        const bookingSearch = new AdminSearch({
            formId: 'booking-search-form',
            inputId: 'booking-search-input',
            resultContainerId: 'booking-table-container',
            countDisplayId: 'booking-count-display',
            apiEndpoint: '/api/admin/bookings',
            searchParam: 'search',
            instantSearch: true,
            debounceTime: 400,
            renderResults: renderBookingResults
        });
    }
    
    /**
     * Renders booking search results
     * @param {Object} data - Booking data from API
     * @param {HTMLElement} container - Container to render results into
     */
    function renderBookingResults(data, container) {
        if (!data.bookings || data.bookings.length === 0) {
            container.innerHTML = `
                <div class="alert alert-info text-center" role="alert">
                    <i class="fas fa-info-circle me-2"></i>
                    No bookings found matching your search criteria.
                </div>
            `;
            return;
        }
        
        // Build HTML for booking table
        let html = `
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Reference</th>
                        <th>User</th>
                        <th>Car</th>
                        <th>Dates</th>
                        <th>Status</th>
                        <th>Total</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        // Add rows for each booking
        data.bookings.forEach(booking => {
            // Determine status badge color
            let statusBadgeClass = 'secondary';
            if (booking.status === 'confirmed') statusBadgeClass = 'success';
            else if (booking.status === 'pending') statusBadgeClass = 'warning';
            else if (booking.status === 'cancelled') statusBadgeClass = 'danger';
            else if (booking.status === 'completed') statusBadgeClass = 'info';
            
            html += `
                <tr>
                    <td>${booking.id}</td>
                    <td><strong>${booking.reference}</strong></td>
                    <td>
                        ${booking.user ? `
                            <div>
                                <strong>${booking.user.name}</strong><br>
                                <small>${booking.user.email}</small>
                            </div>
                        ` : 'N/A'}
                    </td>
                    <td>
                        ${booking.car ? `
                            <div>
                                <strong>${booking.car.make} ${booking.car.model}</strong><br>
                                <small>${booking.car.year}</small>
                            </div>
                        ` : 'N/A'}
                    </td>
                    <td>
                        <div>
                            <small class="d-block">From: ${booking.start_date}</small>
                            <small class="d-block">To: ${booking.end_date}</small>
                        </div>
                    </td>
                    <td>
                        <span class="badge bg-${statusBadgeClass}">
                            ${booking.status.charAt(0).toUpperCase() + booking.status.slice(1)}
                        </span>
                    </td>
                    <td>₱${booking.total_price}</td>
                    <td>
                        <div class="btn-group">
                            <a href="/admin/bookings/${booking.id}" class="btn btn-sm btn-outline-primary">
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
        
        container.innerHTML = html;
    }
}); 