from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models.notification import Notification
from models import db
from models.loan_car import LoanNotification, LoanCar, LoanSale
from models.car import Car
from sqlalchemy import desc, union_all
from sqlalchemy.orm import joinedload, aliased


notification_bp = Blueprint('notification', __name__)

@notification_bp.route('/')
@login_required
def list_notifications():
    """Display all notifications for the current user"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    try:
        # Columns must match in count and name
        columns = [
            'id', 'title', 'message', 'notification_type', 'is_read',
            'created_at', 'booking_id', 'loan_car_id', 'loan_sale_id',
            'loan_payment_id', 'source'
        ]

        # Regular notifications
        regular_notifications = db.session.query(
            Notification.id.label('id'),
            Notification.title.label('title'),
            Notification.message.label('message'),
            Notification.notification_type.label('notification_type'),
            Notification.is_read.label('is_read'),
            Notification.created_at.label('created_at'),
            Notification.booking_id.label('booking_id'),
            db.literal(None).label('loan_car_id'),
            db.literal(None).label('loan_sale_id'),
            db.literal(None).label('loan_payment_id'),
            db.literal('regular').label('source')
        ).filter_by(user_id=current_user.id)

        # Admin-only loan notifications
        if current_user.is_admin:
            loan_notifications = db.session.query(
                LoanNotification.id.label('id'),
                LoanNotification.title.label('title'),
                LoanNotification.message.label('message'),
                LoanNotification.notification_type.label('notification_type'),
                LoanNotification.is_read.label('is_read'),
                LoanNotification.created_at.label('created_at'),
                db.literal(None).label('booking_id'),
                LoanNotification.loan_car_id.label('loan_car_id'),
                LoanNotification.loan_sale_id.label('loan_sale_id'),
                LoanNotification.loan_payment_id.label('loan_payment_id'),
                db.literal('loan').label('source')
            )

            combined_query = union_all(regular_notifications, loan_notifications)
        else:
            combined_query = regular_notifications

        # Wrap in subquery
        subquery = combined_query.subquery()
        final_query = db.session.query(subquery).order_by(desc(subquery.c.created_at))

        all_notifications = final_query.paginate(page=page, per_page=per_page, error_out=False)

        _mark_notifications_as_read()

        return render_template('user/notifications.html', all_notifications=all_notifications)

    except Exception as e:
        flash(f'Error loading notifications: {str(e)}', 'error')
        return render_template('user/notifications.html', all_notifications=None)

def _mark_notifications_as_read():
    """Helper function to mark notifications as read"""
    try:
        # Mark regular notifications as read
        unread_regular = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
        for notification in unread_regular:
            notification.is_read = True
        
        # Mark loan notifications as read (admin only)
        if current_user.is_admin:
            unread_loan = LoanNotification.query.filter_by(is_read=False).all()
            for notification in unread_loan:
                notification.is_read = True
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error marking notifications as read: {str(e)}', 'error')

@notification_bp.route('/unread')
@login_required
def unread_count():
    """Get count of unread notifications for the current user"""
    try:
        regular_count = Notification.get_unread_count(current_user.id)
        loan_count = 0
        
        if current_user.is_admin:
            loan_count = LoanNotification.query.filter_by(is_read=False).count()
        
        total_count = regular_count + loan_count
        return jsonify({'count': total_count})
    except Exception as e:
        return jsonify({'error': str(e), 'count': 0}), 500

@notification_bp.route('/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    """Mark a specific notification as read"""
    try:
        source = request.form.get('source', 'regular')
        
        if source == 'loan':
            if not current_user.is_admin:
                return jsonify({'error': 'Access denied'}), 403
            notification = LoanNotification.query.get_or_404(notification_id)
        else:
            notification = Notification.query.filter_by(
                id=notification_id, 
                user_id=current_user.id
            ).first_or_404()
        
        notification.is_read = True
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True})
        return redirect(url_for('notification.list_notifications'))
        
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': str(e)}), 500
        flash(f'Error marking notification as read: {str(e)}', 'error')
        return redirect(url_for('notification.list_notifications'))

@notification_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications as read for the current user"""
    try:
        # Mark regular notifications as read
        regular_notifications = Notification.query.filter_by(
            user_id=current_user.id, 
            is_read=False
        ).all()
        for notification in regular_notifications:
            notification.is_read = True
        
        # Mark loan notifications as read (admin only)
        if current_user.is_admin:
            loan_notifications = LoanNotification.query.filter_by(is_read=False).all()
            for notification in loan_notifications:
                notification.is_read = True
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@notification_bp.route('/delete/<int:notification_id>', methods=['POST'])
@login_required
def delete_notification(notification_id):
    """Delete a specific notification (regular or loan-based)"""
    try:
        source = request.form.get('source', 'regular')  # 'loan' or 'regular'

        # Handle loan notifications
        if source == 'loan':
            if not current_user.is_admin:
                return jsonify({'error': 'Access denied'}), 403
            notification = LoanNotification.query.get_or_404(notification_id)

        # Handle regular notifications
        else:
            notification = Notification.query.filter_by(
                id=notification_id,
                user_id=current_user.id
            ).first()
            if not notification:
                return jsonify({'error': 'Notification not found'}), 404

        db.session.delete(notification)
        db.session.commit()

        # AJAX response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True})

        flash('Notification deleted successfully.', 'success')
        return redirect(url_for('notification.list_notifications'))

    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': f'Error deleting notification: {str(e)}'}), 500
        flash(f'Error deleting notification: {str(e)}', 'error')
        return redirect(url_for('notification.list_notifications'))


@notification_bp.route('/api/latest')
@login_required
def get_latest_notifications():
    """Get the latest 5 notifications for the current user"""
    try:
        # Get regular notifications
        regular_notifications = db.session.query(
            Notification.id.label("id"),
            Notification.title.label("title"),
            Notification.message.label("message"),
            Notification.notification_type.label("notification_type"),
            Notification.is_read.label("is_read"),
            Notification.created_at.label("created_at"),
            Notification.booking_id.label("booking_id"),
            db.literal(None).label('loan_car_id'),
            db.literal('regular').label('source')
        ).filter_by(user_id=current_user.id)
        
        # Get loan notifications (admin only)
        if current_user.is_admin:
            loan_notifications = db.session.query(
                LoanNotification.id.label("id"),
                LoanNotification.title.label("title"),
                LoanNotification.message.label("message"),
                LoanNotification.notification_type.label("notification_type"),
                LoanNotification.is_read.label("is_read"),
                LoanNotification.created_at.label("created_at"),
                db.literal(None).label('booking_id'),
                LoanNotification.loan_car_id.label('loan_car_id'),  
                db.literal('loan').label('source')
            )
            
            combined_query = union_all(regular_notifications, loan_notifications)
        else:
            combined_query = regular_notifications
        
        # Get latest 5 notifications
        subquery = combined_query.subquery()
        latest_notifications = db.session.query(
            subquery.c.id,
            subquery.c.title,
            subquery.c.message,
            subquery.c.notification_type,
            subquery.c.is_read,
            subquery.c.created_at,
            subquery.c.booking_id,
            subquery.c.loan_car_id,
            subquery.c.source
        ).order_by(
            desc(subquery.c.created_at)
        ).limit(5).all()

                
        notifications_data = []
        for notification in latest_notifications:
            notification_dict = {
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'is_read': notification.is_read,
                'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M'),
                'type': notification.notification_type,
                'booking_id': notification.booking_id,
                'loan_car_id': getattr(notification, 'loan_car_id', None),
                'source': notification.source
            }
            notifications_data.append(notification_dict)
        
        # Get total unread count
        regular_count = Notification.get_unread_count(current_user.id)
        loan_count = 0
        if current_user.is_admin:
            loan_count = LoanNotification.query.filter_by(is_read=False).count()
        
        return jsonify({
            'notifications': notifications_data,
            'unread_count': regular_count + loan_count
        })
        
    except Exception as e:
        
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'notifications': [], 'unread_count': 0}), 500

@notification_bp.route('/api/booking-details/<int:booking_id>')
@login_required
def get_booking_details(booking_id):
    """Get booking details for a notification"""
    try:
        from models.booking import Booking
        from models.car import Car
        from models.user import User
        
        booking = Booking.query.options(
            joinedload(Booking.car),
            joinedload(Booking.user),
            joinedload(Booking.payment)
        ).get_or_404(booking_id)
        
        # Check permissions
        if not current_user.is_admin and booking.user_id != current_user.id:
            return jsonify({'error': 'You do not have permission to view this booking'}), 403
        
        # Get car data
        car_data = None
        if booking.car:
            car_data = {
                'id': booking.car.id,
                'make': booking.car.make,
                'model': booking.car.model,
                'year': booking.car.year,
                'image_url': getattr(booking.car, 'image_url', None),
                'daily_rate': float(booking.car.daily_rate)
            }
        
        # Get user data
        user_data = {
            'id': booking.user.id,
            'name': f"{booking.user.first_name} {booking.user.last_name}",
            'email': booking.user.email
        }
        
        # Get payment data
        payment_data = None
        if booking.payment:
            payment_data = {
                'id': booking.payment.id,
                'amount': float(booking.payment.amount),
                'status': booking.payment.status,
                'payment_method': booking.payment.payment_method,
                'payment_date': booking.payment.payment_date.strftime('%Y-%m-%d %H:%M') if booking.payment.payment_date else None
            }
        
        booking_data = {
            'id': booking.id,
            'reference': booking.get_reference(),
            'booking_date': booking.booking_date.strftime('%Y-%m-%d %H:%M'),
            'created_at': booking.booking_date.strftime('%Y-%m-%d %H:%M'),
            'start_date': booking.start_date.strftime('%Y-%m-%d'),
            'end_date': booking.end_date.strftime('%Y-%m-%d'),
            'status': booking.status,
            'total_cost': float(booking.total_cost),
            'duration_days': getattr(booking, 'duration_days', 0),
            'car': car_data,
            'user': user_data,
            'payment': payment_data,
            'is_returned': getattr(booking, 'returned', False),
            'pickup_location': getattr(booking, 'pickup_location', None)
        }
        
        return jsonify(booking_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notification_bp.route('/api/loan-car-details/<int:loan_car_id>')
@login_required
def get_loan_car_details(loan_car_id):
    """Get loan car details for a notification"""
    try:
        if not current_user.is_admin:
            return jsonify({'error': 'Access denied'}), 403
            
        loan_car = LoanCar.query.options(joinedload(LoanCar.car)).get_or_404(loan_car_id)
        
        if not loan_car.car:
            return jsonify({'error': 'Car not found'}), 404
        
        loan_sale = LoanSale.query.filter_by(loan_car_id=loan_car.id).first()
        
        loan_car_data = {
            'id': loan_car.id,
            'loan_sale_price': float(loan_car.loan_sale_price),
            'commission_rate': float(loan_car.commission_rate),
            'status': loan_car.status,
            'date_offered': loan_car.date_offered.strftime('%Y-%m-%d %H:%M'),
            'activated_at': loan_car.activated_at.strftime('%Y-%m-%d %H:%M') if loan_car.activated_at else None,
            'car': {
                'id': loan_car.car.id,
                'make': loan_car.car.make,
                'model': loan_car.car.model,
                'year': loan_car.car.year,
                'color': getattr(loan_car.car, 'color', None)
            },
            'loan_sale': None
        }
        
        if loan_sale:
            loan_car_data['loan_sale'] = {
                'id': loan_sale.id,
                'first_name': loan_sale.first_name,
                'middle_name': getattr(loan_sale, 'middle_name', None),
                'last_name': loan_sale.last_name,
                'email': loan_sale.email,
                'contact': loan_sale.contact,
                'loan_term': getattr(loan_sale, 'loan_term', None),
                'disbursement_id': getattr(loan_sale, 'disbursement_id', None)
            }
        
        return jsonify(loan_car_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notification_bp.route('/booking-redirect/<int:booking_id>')
@login_required
def booking_redirect(booking_id):
    """Redirect to the proper booking details page based on user role"""
    try:
        # Verify booking exists and user has access
        from models.booking import Booking
        booking = Booking.query.get_or_404(booking_id)
        
        if not current_user.is_admin and booking.user_id != current_user.id:
            flash('You do not have permission to view this booking.', 'error')
            return redirect(url_for('notification.list_notifications'))
        
        if current_user.is_admin:
            return redirect(url_for('admin.booking_details', booking_id=booking_id))
        return redirect(url_for('user.booking_details', booking_id=booking_id))
        
    except Exception as e:
        flash(f'Error accessing booking: {str(e)}', 'error')
        return redirect(url_for('notification.list_notifications'))
    