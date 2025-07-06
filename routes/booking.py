from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime

from models import db
from models.booking import Booking
from models.car import Car

booking = Blueprint('booking', __name__)

@booking.route('/bookings/active')
@login_required
def active_bookings():
    active_bookings = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.status == 'confirmed',
        Booking.returned == False
    ).all()
    
    return render_template('booking/active_bookings.html', bookings=active_bookings, now=datetime.now())

@booking.route('/bookings/past')
@login_required
def past_bookings():
    past_bookings = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.status.in_(['completed', 'cancelled'])
    ).order_by(Booking.booking_date.desc()).all()
    
    return render_template('booking/past_bookings.html', bookings=past_bookings)

@booking.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    # Check if the current user is an admin
    if current_user.is_admin:
        flash('Admin users should manage bookings through the admin panel.', 'warning')
        return redirect(url_for('admin.booking_details', booking_id=booking_id))
    
    booking = Booking.query.get_or_404(booking_id)
    
    # Check if the booking belongs to the current user
    if booking.user_id != current_user.id:
        flash('You do not have permission to cancel this booking.', 'danger')
        return redirect(url_for('user.booking_history'))
    
    # Check if the booking can be cancelled
    if booking.status != 'pending' and booking.status != 'confirmed':
        flash('This booking cannot be cancelled.', 'danger')
        return redirect(url_for('user.booking_details', booking_id=booking_id))
    
    if booking.start_date <= datetime.now().date():
        flash('Bookings that have already started cannot be cancelled.', 'danger')
        return redirect(url_for('user.booking_details', booking_id=booking_id))
    
    # Update booking status and car availability
    booking.status = 'cancelled'
    car = Car.query.get(booking.car_id)
    car.is_available = True
<<<<<<< HEAD
    
=======
    car.status = 'available'  # Reset car status to available
    car.bookings.remove(booking)  # Remove booking from car's bookings
    db.session.add(car)  # Add car back to session to update its status
>>>>>>> 8a8ec6c (fixed some bugs on status, modified the api, fixed some routings, and some logics)
    db.session.commit()
    
    flash('Booking cancelled successfully.', 'success')
    return redirect(url_for('user.booking_history')) 