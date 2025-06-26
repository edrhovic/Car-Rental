/**
 * Admin Payment Search - AJAX Implementation
 * Enhances the payment management search with AJAX functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize payment search if elements exist
    if (document.getElementById('payment-search-form')) {
        const paymentSearch = new AdminSearch({
            formId: 'payment-search-form',
            inputId: 'payment-search-input',
            resultContainerId: 'payment-table-container',
            countDisplayId: 'payment-count-display',
            apiEndpoint: '/api/admin/payments',
            searchParam: 'search',
            instantSearch: true,
            debounceTime: 400,
            renderResults: renderPaymentResults
        });
    }
    
    /**
     * Renders payment search results
     * @param {Object} data - Payment data from API
     * @param {HTMLElement} container - Container to render results into
     */
    function renderPaymentResults(data, container) {
        // Update payment statistics if available
        if (data.stats) {
            updatePaymentStats(data.stats);
        }
        
        if (!data.payments || data.payments.length === 0) {
            container.innerHTML = `
                <div class="alert alert-info text-center" role="alert">
                    <i class="fas fa-info-circle me-2"></i>
                    No payments found matching your search criteria.
                </div>
            `;
            return;
        }
        
        // Build HTML for payment table
        let html = `
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Date</th>
                        <th>Customer</th>
                        <th>Type</th>
                        <th>Amount</th>
                        <th>Method</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        // Add rows for each payment
        data.payments.forEach(payment => {
            // Determine status badge color
            let statusBadgeClass = 'secondary';
            if (payment.status === 'completed') statusBadgeClass = 'success';
            else if (payment.status === 'pending') statusBadgeClass = 'warning';
            else if (payment.status === 'failed') statusBadgeClass = 'danger';
            else if (payment.status === 'refunded') statusBadgeClass = 'info';
            
            html += `
                <tr>
                    <td>${payment.id}</td>
                    <td>${payment.payment_date}</td>
                    <td>
                        ${payment.user ? `
                            <div>
                                <strong>${payment.user.name}</strong><br>
                                <small>${payment.user.email}</small>
                            </div>
                        ` : 'N/A'}
                    </td>
                    <td>
                        <span class="badge bg-${payment.is_late_fee ? 'danger' : 'info'}">
                            ${payment.is_late_fee ? 'Late Fee' : 'Booking'}
                        </span>
                    </td>
                    <td><strong>₱${payment.amount}</strong></td>
                    <td>${payment.payment_method}</td>
                    <td>
                        <span class="badge bg-${statusBadgeClass}">
                            ${payment.status.charAt(0).toUpperCase() + payment.status.slice(1)}
                        </span>
                    </td>
                    <td>
                        <div class="btn-group">
                            <a href="/admin/payments/${payment.id}" class="btn btn-sm btn-outline-primary">
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
    
    /**
     * Updates payment statistics display
     * @param {Object} stats - Payment statistics from API
     */
    function updatePaymentStats(stats) {
        const totalRevenueEl = document.querySelector('.total-revenue');
        const totalPendingEl = document.querySelector('.total-pending');
        const totalTransactionsEl = document.querySelector('.total-transactions');
        
        if (totalRevenueEl) {
            totalRevenueEl.textContent = `₱${stats.total_revenue.toFixed(2)}`;
        }
        
        if (totalPendingEl) {
            totalPendingEl.textContent = `₱${stats.total_pending.toFixed(2)}`;
        }
        
        if (totalTransactionsEl) {
            totalTransactionsEl.textContent = stats.total_payments.toString();
        }
    }
}); 