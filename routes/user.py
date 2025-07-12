from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from werkzeug.security import generate_password_hash
from functools import wraps
import uuid

from models import db
from models.user import User
from models.booking import Booking
from models.review import Review
from models.payment import Payment
from models.notification import Notification
from models.car import Car

user = Blueprint('user', __name__)

# Middleware to check if user is not an admin
def non_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_admin:
            flash('Admin users do not have access to booking features.', 'warning')
            return redirect(url_for('user.profile'))
        return f(*args, **kwargs)
    return decorated_function

@user.route('/profile')
@login_required
def profile():
    return render_template('user/profile.html', user=current_user)

@user.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        # Track what fields were changed
        changed_fields = []
        
        if current_user.first_name != request.form.get('first_name'):
            changed_fields.append("first name")
            current_user.first_name = request.form.get('first_name')
            
        if current_user.last_name != request.form.get('last_name'):
            changed_fields.append("last name")
            current_user.last_name = request.form.get('last_name')
            
        if current_user.phone_number != request.form.get('phone_number'):
            changed_fields.append("phone number")
            current_user.phone_number = request.form.get('phone_number')
            
        if current_user.address != request.form.get('address'):
            changed_fields.append("address")
            current_user.address = request.form.get('address')
            
        if current_user.driver_license != request.form.get('driver_license'):
            changed_fields.append("driver license")
            current_user.driver_license = request.form.get('driver_license')
        
        # Update password if provided
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password and password == confirm_password:
            current_user.password_hash = generate_password_hash(password)
            changed_fields.append("password")
        
        db.session.commit()
        
        # Create admin notification if any fields were changed
        if changed_fields:
            # Format the changed fields into a readable string
            changes_str = ", ".join(changed_fields)
            
            # Create notification for admin
            Notification.create_admin_profile_notification(
                current_user.id,
                f"{current_user.first_name} {current_user.last_name}",
                changes_str
            )
        
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('user.profile'))
    
    return render_template('user/edit_profile.html', user=current_user)

@user.route('/bookings')
@login_required
@non_admin_required
def booking_history():
    # Get filter parameters
    status = request.args.get('status', '')
    sort = request.args.get('sort', 'date_desc')
    
    # Start with base query
    query = Booking.query.filter_by(user_id=current_user.id)
    
    # Apply status filter if provided
    if status:
        query = query.filter(Booking.status == status)
    
    # Apply sorting
    if sort == 'date_asc':
        query = query.order_by(Booking.booking_date.asc())
    elif sort == 'date_desc':
        query = query.order_by(Booking.booking_date.desc())
    elif sort == 'car':
        # Join with Car table to sort by car name
        query = query.join(Car).order_by(Car.make.asc(), Car.model.asc())
    elif sort == 'price_desc':
        query = query.order_by(Booking.total_cost.desc())
    elif sort == 'price_asc':
        query = query.order_by(Booking.total_cost.asc())
    else:
        # Default sorting by booking date (newest first)
        query = query.order_by(Booking.booking_date.desc())
    
    # Execute query
    bookings = query.all()
    
    return render_template('user/booking_history.html', bookings=bookings)

@user.route('/bookings/<int:booking_id>')
@login_required
@non_admin_required
def booking_details(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Check if the booking belongs to the current user
    if booking.user_id != current_user.id:
        flash('You do not have permission to view this booking.', 'danger')
        return redirect(url_for('user.booking_history'))
    
    return render_template('user/booking_details.html', booking=booking)

@user.route('/bookings/<int:booking_id>/review', methods=['GET', 'POST'])
@login_required
@non_admin_required
def add_review(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Check if the booking belongs to the current user
    if booking.user_id != current_user.id:
        flash('You do not have permission to review this booking.', 'danger')
        return redirect(url_for('user.booking_history'))
    
    # Check if the booking is completed and the car has been returned
    if booking.status != 'completed' or not booking.returned:
        flash('You can only review completed bookings.', 'danger')
        return redirect(url_for('user.booking_details', booking_id=booking_id))
    
    # Check if a review already exists
    existing_review = Review.query.filter_by(booking_id=booking_id).first()
    if existing_review:
        flash('You have already reviewed this booking.', 'danger')
        return redirect(url_for('user.booking_details', booking_id=booking_id))
    
    if request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('comment')
        
        review = Review(
            user_id=current_user.id,
            car_id=booking.car_id,
            booking_id=booking_id,
            rating=rating,
            comment=comment
        )
        
        db.session.add(review)
        db.session.commit()
        
        flash('Your review has been submitted.', 'success')
        return redirect(url_for('user.booking_details', booking_id=booking_id))
    
    return render_template('user/add_review.html', booking=booking)

@user.route('/late-fees')
@login_required
@non_admin_required
def late_fees():
    """View all late fees for the current user"""
    # Get all late fees for the current user
    late_fees = Payment.query.filter_by(
        user_id=current_user.id,
        is_late_fee=True
    ).filter(Payment.status != 'paid').all()
    
    print(f"Found {len(late_fees)} late fees for user {current_user.id}")
    for fee in late_fees:
        print(f"Late fee: {fee.id}, Amount: {fee.amount}, Status: {fee.status}")
    
    # Get recent payment history (last 5 completed payments)
    recent_payments = Payment.query.filter_by(
        user_id=current_user.id
    ).filter(Payment.status == 'paid').order_by(Payment.payment_date.desc()).limit(5).all()
    
    print(f"Found {len(recent_payments)} recent payments for user {current_user.id}")
    
    return render_template('user/late_fees.html', late_fees=late_fees, recent_payments=recent_payments)

@user.route('/late-fees/<int:payment_id>/pay', methods=['GET', 'POST'])
@login_required
@non_admin_required
def pay_late_fee(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    print(f"Processing payment for late fee: {payment_id}, amount: {payment.amount}")
    
    if not payment.booking_id:
        flash('Invalid payment record. Booking information not found.', 'danger')
        return redirect(url_for('user.late_fees'))
        
    try:
        booking = Booking.query.get(payment.booking_id)
        print(f"Found booking: {booking.id}, reference: {booking.get_reference()}")
    except Exception as e:
        print(f"Error retrieving booking: {str(e)}")
        flash('Error retrieving booking information.', 'danger')
        return redirect(url_for('user.late_fees'))
    
    if payment.user_id != current_user.id:
        flash('You do not have permission to access this payment.', 'danger')
        return redirect(url_for('user.late_fees'))
    
    if payment.status == 'paid':
        flash('This late fee has already been paid.', 'info')
        return redirect(url_for('user.late_fees'))
    
    if request.method == 'POST':
        print("Processing POST request for late fee payment")
        payment_method = request.form.get('payment_method')
        print(f"Payment method selected: {payment_method}")
        
        # Get card information from form
        card_holder = request.form.get('card_holder', '')
        card_number = request.form.get('card_number', '')
        expiry_date = request.form.get('expiry_date', '')
        
        # Process card number for storage
        card_last_four = ''
        if card_number:
            # Remove spaces and get last 4 digits
            card_number_clean = card_number.replace(' ', '')
            card_last_four = card_number_clean[-4:] if len(card_number_clean) >= 4 else ''
        
        # Determine card type based on payment method
        card_type = payment_method.replace('_', ' ').title() if payment_method in ['credit_card', 'debit_card'] else None
        
        # Process the payment
        payment.payment_method = payment_method
        payment.status = 'paid'
        payment.payment_date = datetime.now()
        
        # Store card information for admin viewing
        payment.card_holder_name = card_holder if card_holder else None
        payment.card_number = card_number if card_number else None
        payment.card_last_four = card_last_four if card_last_four else None
        payment.card_expiry = expiry_date if expiry_date else None
        payment.card_type = card_type
        
        # Update the related booking's late fee status
        if booking:
            booking.late_fee_paid = True
        
        try:
            db.session.commit()
            
            # Create notification for admin about the late fee payment
            user_name = f"{current_user.first_name} {current_user.last_name}"
            booking_ref = booking.get_reference() if booking else "N/A"
            
            Notification.create_admin_payment_notification(
                booking_id=booking.id,
                user_name=user_name,
                amount=payment.amount,
                payment_type='late_fee',
                booking_reference=booking_ref
            )
            
            print(f"Successfully processed late fee payment: {payment_id}")
            flash('Late fee payment successful!', 'success')
            return redirect(url_for('user.late_fees'))
        except Exception as e:
            db.session.rollback()
            print(f"Error processing late fee payment: {str(e)}")
            flash(f'An error occurred: {str(e)}', 'danger')
    
    return render_template('user/pay_late_fee.html', payment=payment, booking=booking)

@user.route('/payment-history')
@login_required
def payment_history():
    """View payment history for the current user"""
    # Get all payments for the current user
    payments = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.payment_date.desc()).all()
    
    print(f"Found {len(payments)} total payments for user {current_user.id}")
    for payment in payments:
        print(f"Payment ID: {payment.id}, Method: {payment.payment_method}, Amount: {payment.amount}")
        if payment.booking:
            booking_ref = payment.booking.get_reference()
            print(f"  Booking: {payment.booking_id}, Reference: {booking_ref}")
        else:
            print(f"  No booking associated with payment {payment.id}")
    
    return render_template('user/payment_history.html', payments=payments)

@user.route('/api/user/late-fees-summary')
@login_required
@non_admin_required
def late_fees_summary_api():
    """API endpoint to get a summary of user's late fees for AJAX calls"""
    # Get pending late fees for the current user
    late_fees = Payment.query.filter_by(
        user_id=current_user.id,
        is_late_fee=True,
        status='pending'
    ).all()
    
    # Calculate total amount
    total_amount = sum(fee.amount for fee in late_fees)
    
    # Return JSON response
    return jsonify({
        'count': len(late_fees),
        'total_amount': float(total_amount),
        'has_fees': len(late_fees) > 0
    }) 