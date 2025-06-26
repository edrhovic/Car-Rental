/**
 * JDM Car Rentals - Notifications System
 * Handles the fetching and display of user notifications
 */

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const notificationBadge = document.getElementById('notification-badge');
    const notificationMenu = document.getElementById('notification-menu');
    const notificationList = document.getElementById('notification-list');
    const loadingSpinner = document.getElementById('notification-loading');
    const notificationDropdown = document.getElementById('notificationDropdown');
    const viewAllBtn = document.getElementById('view-all-notifications');

    // Variables
    let isInitialized = false;
    
    // Check if the current user is an admin
    const isAdmin = document.body.classList.contains('admin-user');
    
    // Initialize the notification system
    function initNotifications() {
        if (isInitialized) return;
        isInitialized = true;
        
        // Initial check for unread notifications count
        updateUnreadCount();
        
        // Set up polling for new notifications (every 60 seconds)
        setInterval(updateUnreadCount, 60000);
        
        // Load notifications when dropdown is opened
        if (notificationDropdown) {
            notificationDropdown.addEventListener('shown.bs.dropdown', function() {
                loadNotifications();
            });
        }
        
        // Mark notification as read when clicked
        if (notificationList) {
            notificationList.addEventListener('click', function(event) {
                const target = event.target.closest('.notification-item');
                if (target && !target.classList.contains('read')) {
                    const notificationId = target.dataset.id;
                    markAsRead(notificationId);
                }
            });
        }
    }
    
    // Update the unread notifications count
    function updateUnreadCount() {
        fetch('/notification/unread')
            .then(response => response.json())
            .then(data => {
                if (notificationBadge) {
                    if (data.count > 0) {
                        notificationBadge.textContent = data.count;
                        notificationBadge.classList.remove('d-none');
                        
                        // Add animation to the bell icon
                        const bellIcon = document.querySelector('#notificationDropdown i.fa-bell');
                        if (bellIcon) {
                            bellIcon.classList.add('bell-animated');
                        }
                    } else {
                        notificationBadge.classList.add('d-none');
                        
                        // Remove animation if no unread notifications
                        const bellIcon = document.querySelector('#notificationDropdown i.fa-bell');
                        if (bellIcon) {
                            bellIcon.classList.remove('bell-animated');
                        }
                    }
                }
            })
            .catch(error => console.error('Error fetching notification count:', error));
    }
    
    // Load notifications for the dropdown
    function loadNotifications() {
        if (loadingSpinner) loadingSpinner.classList.remove('d-none');
        if (notificationList) notificationList.innerHTML = '';
        
        fetch('/notification/api/latest')
            .then(response => response.json())
            .then(data => {
                if (loadingSpinner) loadingSpinner.classList.add('d-none');
                displayNotifications(data.notifications);
                
                // Update badge with latest count
                if (notificationBadge) {
                    if (data.unread_count > 0) {
                        notificationBadge.textContent = data.unread_count;
                        notificationBadge.classList.remove('d-none');
                    } else {
                        notificationBadge.classList.add('d-none');
                    }
                }
            })
            .catch(error => {
                console.error('Error fetching notifications:', error);
                if (loadingSpinner) loadingSpinner.classList.add('d-none');
                if (notificationList) {
                    notificationList.innerHTML = '<div class="text-center p-3">Failed to load notifications</div>';
                }
            });
    }
    
    // Display notifications in the dropdown
    function displayNotifications(notifications) {
        if (!notificationList) return;
        
        if (notifications.length === 0) {
            notificationList.innerHTML = `
                <div class="notifications-empty-state">
                    <i class="fas fa-bell-slash"></i>
                    <h6>No Notifications</h6>
                    <p class="mb-0">You're all caught up!</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        notifications.forEach(notification => {
            let icon = 'bell';
            let bgColor = 'bg-secondary';
            
            if (notification.type === 'booking_status') {
                icon = 'calendar-check';
                bgColor = 'bg-primary';
            } else if (notification.type === 'payment') {
                icon = 'money-bill-wave';
                bgColor = 'bg-warning';
            }
            
            // Create modal trigger for booking notifications instead of direct links
            let linkAttributes = '';
            if (notification.booking_id) {
                // Use data attributes to trigger modal with booking ID
                linkAttributes = `href="javascript:void(0);" onclick="loadBookingDetails(${notification.booking_id});"`;
            } else if (notification.type === 'system') {
                // For system notifications like contact form submissions
                linkAttributes = `href="/notification"`;
                if (notification.title.includes('Contact Form') && isAdmin) {
                    // For contact form submissions, direct admin to the messages page
                    linkAttributes = `href="/contact/admin/messages"`;
                }
            } else {
                linkAttributes = `href="/notification"`;
            }
            
            html += `
                <a ${linkAttributes} 
                   class="dropdown-item notification-item ${notification.is_read ? 'read' : ''}" 
                   data-id="${notification.id}">
                    <div class="d-flex align-items-center">
                        <div class="notification-icon-container me-3">
                            <span class="notification-icon ${bgColor} text-white">
                                <i class="fas fa-${icon}"></i>
                            </span>
                        </div>
                        <div class="flex-grow-1">
                            <h6 class="mb-0">${notification.title}</h6>
                            <p class="mb-0 small">${notification.message}</p>
                            <small class="text-muted">${notification.created_at}</small>
                        </div>
                        ${!notification.is_read ? '<span class="badge bg-success">New</span>' : ''}
                    </div>
                </a>
                <div class="dropdown-divider"></div>
            `;
        });
        
        // Remove the last divider
        html = html.replace(/<div class="dropdown-divider"><\/div>$/, '');
        
        // Add "View All" button
        html += `
            <div class="text-center p-2">
                <a href="/notification" class="btn btn-sm btn-primary w-100">View All Notifications</a>
            </div>
        `;
        
        notificationList.innerHTML = html;
    }
    
    // Mark a notification as read
    function markAsRead(notificationId) {
        fetch(`/notification/mark-read/${notificationId}`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update UI to show notification as read
                const notificationItem = document.querySelector(`.notification-item[data-id="${notificationId}"]`);
                if (notificationItem) {
                    notificationItem.classList.add('read');
                    const badge = notificationItem.querySelector('.badge');
                    if (badge) badge.remove();
                }
                
                // Update unread count
                updateUnreadCount();
            }
        })
        .catch(error => console.error('Error marking notification as read:', error));
    }
    
    // Mark all notifications as read
    function markAllNotificationsAsRead() {
        fetch('/notification/mark-all-read', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update UI in the notifications list page
                document.querySelectorAll('.notification.unread').forEach(notification => {
                    notification.classList.remove('unread');
                    const badge = notification.querySelector('.badge.bg-success');
                    if (badge) badge.remove();
                });

                // Update UI in the dropdown
                document.querySelectorAll('.notification-item:not(.read)').forEach(notification => {
                    notification.classList.add('read');
                    const badge = notification.querySelector('.badge');
                    if (badge) badge.remove();
                });
                
                // Update the notification badge count
                updateUnreadCount();
                
                // Hide the notification badge in the header
                const notificationBadge = document.getElementById('notification-badge');
                if (notificationBadge) {
                    notificationBadge.classList.add('d-none');
                }
                
                // Optionally reload the notifications in the dropdown to show updated state
                loadNotifications();
            }
        })
        .catch(error => console.error('Error marking all notifications as read:', error));
    }
    
    // Make markAllNotificationsAsRead available globally
    window.markAllNotificationsAsRead = markAllNotificationsAsRead;
    
    // Initialize if user is logged in
    const userDropdown = document.getElementById('userDropdown');
    if (userDropdown) {
        initNotifications();
    }
    
    // Load booking details into modal
    window.loadBookingDetails = function(bookingId) {
        // Get modal elements
        const modal = new bootstrap.Modal(document.getElementById('bookingDetailsModal'));
        const loadingDiv = document.getElementById('booking-modal-loading');
        const contentDiv = document.getElementById('booking-details-content');
        const fullDetailsLink = document.getElementById('modal-view-full-details');
        
        // Show modal with loading state
        modal.show();
        loadingDiv.classList.remove('d-none');
        contentDiv.classList.add('d-none');
        
        // Set correct URL for full details button based on user role
        const detailsUrl = `/notification/booking-redirect/${bookingId}`;
        
        // Log URL for debugging purposes
        console.log('Setting URL for booking details redirect:', detailsUrl);
        console.log('Booking ID:', bookingId);
        
        fullDetailsLink.href = detailsUrl;
        
        // Fetch booking details
        fetch(`/notification/api/booking-details/${bookingId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load booking details');
                }
                return response.json();
            })
            .then(data => {
                // Hide loading, show content
                loadingDiv.classList.add('d-none');
                contentDiv.classList.remove('d-none');
                
                // Populate modal with booking data
                document.getElementById('modal-booking-id').textContent = data.id;
                document.getElementById('modal-booking-reference').textContent = data.reference;
                document.getElementById('modal-booking-date').textContent = data.booking_date;
                
                // Set status with appropriate badge
                let statusBadge = '';
                switch(data.status) {
                    case 'pending':
                        statusBadge = '<span class="badge bg-warning">Pending</span>';
                        break;
                    case 'confirmed':
                        statusBadge = '<span class="badge bg-success">Confirmed</span>';
                        break;
                    case 'active':
                        statusBadge = '<span class="badge bg-primary">Active</span>';
                        break;
                    case 'completed':
                        statusBadge = '<span class="badge bg-info">Completed</span>';
                        break;
                    case 'cancelled':
                        statusBadge = '<span class="badge bg-danger">Cancelled</span>';
                        break;
                    case 'pending_return':
                        statusBadge = '<span class="badge bg-warning">Pending Return</span>';
                        break;
                    default:
                        statusBadge = '<span class="badge bg-secondary">' + data.status + '</span>';
                }
                document.getElementById('modal-booking-status').innerHTML = statusBadge;
                
                // Rental period
                document.getElementById('modal-rental-period').textContent = 
                    `${data.start_date} to ${data.end_date}`;
                
                // Duration and cost
                document.getElementById('modal-duration').textContent = `${data.duration_days} days`;
                document.getElementById('modal-total-cost').textContent = `₱${data.total_cost.toFixed(2)}`;
                
                // Car details
                document.getElementById('modal-car-name').textContent = 
                    `${data.car.year} ${data.car.make} ${data.car.model}`;
                document.getElementById('modal-daily-rate').textContent = data.car.daily_rate.toFixed(2);
                document.getElementById('modal-location').textContent = data.pickup_location || 'Not specified';
                document.getElementById('modal-car-link').href = `/cars/${data.car.id}`;
                
                // Car image
                const carImage = document.getElementById('modal-car-image');
                if (data.car.image_url) {
                    carImage.src = data.car.image_url;
                    carImage.style.display = 'block';
                } else {
                    carImage.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Error loading booking details:', error);
                
                // Show error in modal instead of redirecting
                loadingDiv.classList.add('d-none');
                contentDiv.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        <span>Unable to load booking details. Please try again or view full details.</span>
                    </div>
                    <div class="text-center mt-3">
                        <button type="button" class="btn btn-secondary me-2" data-bs-dismiss="modal">Close</button>
                        <a href="${detailsUrl}" class="btn btn-primary">View Full Details</a>
                    </div>
                `;
                contentDiv.classList.remove('d-none');
            });
    };
}); 