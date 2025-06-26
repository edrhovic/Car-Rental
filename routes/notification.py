from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models.notification import Notification
from models import db

notification_bp = Blueprint('notification', __name__)

@notification_bp.route('/')
@login_required
def list_notifications():
    """Display all notifications for the current user"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get notifications for the current user, sorted by creation date (newest first)
    notifications = Notification.query.filter_by(user_id=current_user.id) \
        .order_by(Notification.created_at.desc()) \
        .paginate(page=page, per_page=per_page)
    
    # Mark all unread notifications as read when user views them
    unread_notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    for notification in unread_notifications:
        notification.is_read = True
    db.session.commit()
    
    return render_template('user/notifications.html', notifications=notifications)

@notification_bp.route('/unread')
@login_required
def unread_count():
    """Get count of unread notifications for the current user (AJAX endpoint)"""
    count = Notification.get_unread_count(current_user.id)
    return jsonify({'count': count})

@notification_bp.route('/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    """Mark a specific notification as read"""
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    notification.is_read = True
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    return redirect(url_for('notification.list_notifications'))

@notification_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications as read for the current user"""
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    for notification in notifications:
        notification.is_read = True
    db.session.commit()
    return jsonify({'success': True})

@notification_bp.route('/delete/<int:notification_id>', methods=['POST'])
@login_required
def delete_notification(notification_id):
    """Delete a specific notification"""
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    db.session.delete(notification)
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    flash('Notification deleted.', 'success')
    return redirect(url_for('notification.list_notifications'))

@notification_bp.route('/api/latest')
@login_required
def get_latest_notifications():
    """Get the latest 5 notifications for the current user (AJAX endpoint)"""
    latest_notifications = Notification.query.filter_by(user_id=current_user.id) \
        .order_by(Notification.created_at.desc()) \
        .limit(5).all()
    
    notifications_data = [{
        'id': notification.id,
        'title': notification.title,
        'message': notification.message,
        'is_read': notification.is_read,
        'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M'),
        'type': notification.notification_type,
        'booking_id': notification.booking_id
    } for notification in latest_notifications]
    
    return jsonify({
        'notifications': notifications_data,
        'unread_count': Notification.get_unread_count(current_user.id)
    })

@notification_bp.route('/api/booking-details/<int:booking_id>')
@login_required
def get_booking_details(booking_id):
    """Get booking details for a notification (AJAX endpoint)"""
    from models.booking import Booking
    from models.car import Car
    from models.user import User
    
    booking = Booking.query.get_or_404(booking_id)
    
    # Make sure the user has permission to view this booking
    if not current_user.is_admin and booking.user_id != current_user.id:
        return jsonify({'error': 'You do not have permission to view this booking'}), 403
    
    # Get car details
    car = Car.query.get(booking.car_id) if booking.car_id else None
    car_data = None
    if car:
        car_data = {
            'id': car.id,
            'make': car.make,
            'model': car.model,
            'year': car.year,
            'image_url': car.image_url,
            'daily_rate': float(car.daily_rate)
        }
    
    # Get user details
    user = User.query.get(booking.user_id)
    user_data = {
        'id': user.id,
        'name': f"{user.first_name} {user.last_name}",
        'email': user.email
    }
    
    # Get payment details if available
    payment_data = None
    if booking.payment:
        payment_data = {
            'id': booking.payment.id,
            'amount': float(booking.payment.amount),
            'status': booking.payment.status,
            'payment_method': booking.payment.payment_method,
            'payment_date': booking.payment.payment_date.strftime('%Y-%m-%d %H:%M') if booking.payment.payment_date else None
        }
    
    # Prepare data for response
    booking_data = {
        'id': booking.id,
        'reference': booking.get_reference(),
        'booking_date': booking.booking_date.strftime('%Y-%m-%d %H:%M'),
        'created_at': booking.booking_date.strftime('%Y-%m-%d %H:%M'),  # For compatibility with JS
        'start_date': booking.start_date.strftime('%Y-%m-%d'),
        'end_date': booking.end_date.strftime('%Y-%m-%d'),
        'status': booking.status,
        'total_cost': float(booking.total_cost),
        'duration_days': booking.duration_days,
        'car': car_data,
        'user': user_data,
        'payment': payment_data,
        'is_returned': booking.returned,
        'pickup_location': booking.pickup_location
    }
    
    return jsonify(booking_data)

@notification_bp.route('/booking-redirect/<int:booking_id>')
@login_required
def booking_redirect(booking_id):
    """Redirect to the proper booking details page based on user role"""
    # Check if admin
    if current_user.is_admin:
        return redirect(url_for('admin.booking_details', booking_id=booking_id))
    # Otherwise, redirect to user booking details
    return redirect(url_for('user.booking_details', booking_id=booking_id)) 