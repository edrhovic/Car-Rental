from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify, current_app, abort
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta

from models import db
from models.car import Car
from models.booking import Booking
from models.payment import Payment
from models.review import Review
from models.loan_car import LoanCar
import os
import uuid
from werkzeug.utils import secure_filename
from models.notification import Notification
from models.user import User

car = Blueprint('car', __name__)

@car.route('/cars')
def car_list():
    # Get search and filter parameters
    search_query = request.args.get('search', '')
    sort = request.args.get('sort', '')
    transmission = request.args.get('transmission', '')
    fuel_type = request.args.get('fuel_type', '')
    make = request.args.get('make', '')
    
    # Start with base query
    query = Car.query.filter_by(is_available=True, status='available')
    
    # Apply search filter if provided 
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(
            db.or_(
                Car.make.ilike(search_term),
                Car.model.ilike(search_term),
                Car.description.ilike(search_term)
            )
        )
    
    # Apply additional filters
    if transmission:
        query = query.filter(Car.transmission == transmission)
    
    if fuel_type:
        query = query.filter(Car.fuel_type == fuel_type)
    
    if make:
        query = query.filter(Car.make == make)
    
    # Get all available makes for filter dropdown
    # This could be optimized in a production environment with caching
    available_makes = db.session.query(Car.make).distinct().order_by(Car.make).all()
    available_makes = [make[0] for make in available_makes]
    
    # Get all available transmissions for filter dropdown
    available_transmissions = db.session.query(Car.transmission).distinct().order_by(Car.transmission).all()
    available_transmissions = [transmission[0] for transmission in available_transmissions]
    
    # Get all available fuel types for filter dropdown
    available_fuel_types = db.session.query(Car.fuel_type).distinct().order_by(Car.fuel_type).all()
    available_fuel_types = [fuel_type[0] for fuel_type in available_fuel_types]
    
    # Apply sorting if specified
    if sort == 'price_asc':
        query = query.order_by(Car.daily_rate.asc())
    elif sort == 'price_desc':
        query = query.order_by(Car.daily_rate.desc())
    elif sort == 'year_desc':
        query = query.order_by(Car.year.desc())
    elif sort == 'year_asc':
        query = query.order_by(Car.year.asc())
    else:
        # Default sorting by newest cars
        query = query.order_by(Car.year.desc())
    
    # Execute query
    cars = query.all()
    
    return render_template('car/car_list.html', 
                          cars=cars, 
                          search_query=search_query,
                          current_sort=sort,
                          available_makes=available_makes,
                          available_transmissions=available_transmissions,
                          available_fuel_types=available_fuel_types)

@car.route('/cars/<int:car_id>')
def car_details(car_id):
    car = Car.query.get_or_404(car_id)
    
    # Get related cars (same make or similar price range)
    related_cars = Car.query.filter(
        (Car.make == car.make)
    ).filter(
        Car.id != car.id
    ).limit(3).all()
    
    # Get today's date for min attribute in date inputs
    today = date.today().strftime('%Y-%m-%d')
    
    return render_template('car/car_details.html', car=car, related_cars=related_cars, today=today)

@car.route('/cars/<int:car_id>/book', methods=['GET', 'POST'])
@login_required
def book_car(car_id):
    # Check if the current user is an admin and prevent them from booking
    if current_user.is_admin:
        flash('Admin users are not allowed to book cars. Please use a regular user account.', 'warning')
        return redirect(url_for('car.car_details', car_id=car_id))
    
    car = Car.query.get_or_404(car_id)
    if not car.is_available or car.status != 'available':
        status_messages = {
            'booked': 'This car is currently booked by another customer.',
            'offered_for_loan': 'This car is currently offered for loan and not available for rental.',  # Changed key
            'maintenance': 'This car is currently under maintenance.',
        }
        message = status_messages.get(car.status, 'This car is not available for booking.')
        flash(message, 'danger')
        return redirect(url_for('car.car_details', car_id=car_id))
    
    if request.method == 'POST':
        # Get booking details from the form
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
        branch_location = request.form.get('branch_location')
        
        # Create locations JSON data - use same location for pickup and return
        branch_info = {
            "name": branch_location,
            "address": get_branch_address(branch_location),
            "hours": get_branch_hours(branch_location),
            "contact": get_branch_contact(branch_location)
        }
        
        locations_data = {
            "pickup": branch_info,
            "return": branch_info  # Same location for both pickup and return
        }
        
        # Validate date range
        if start_date < date.today():
            flash('Start date cannot be in the past.', 'danger')
            return redirect(url_for('car.book_car', car_id=car_id))
            
        if end_date < start_date:
            flash('End date must be after start date.', 'danger')
            return redirect(url_for('car.book_car', car_id=car_id))
            
        # Calculate total days and cost
        delta = end_date - start_date
        days = delta.days + 1  # Include both start and end days
        total_cost = days * car.daily_rate
        
        # Create booking
        booking = Booking(
            user_id=current_user.id,
            car_id=car_id,
            start_date=start_date,
            end_date=end_date,
            locations=locations_data,
            total_cost=total_cost,
            status='pending'
        )
        
        db.session.add(booking)
        db.session.commit()
        
        # Create notification for admin users about the new booking
        user_name = f"{current_user.first_name} {current_user.last_name}"
        car_name = car.make + " " + car.model
        
        # Create admin notification
        Notification.create_admin_booking_notification(
            booking_id=booking.id,
            user_name=user_name,
            car_name=car_name,
            booking_reference=booking.get_reference()
        )
        
        # Create notification for the user who made the booking
        Notification.create_booking_notification(
            user_id=current_user.id,
            booking_id=booking.id,
            booking_status='pending',
            booking_reference=booking.get_reference()
        )
        
        # Store booking ID in session for payment
        session['booking_id'] = booking.id
        
        return redirect(url_for('car.payment', booking_id=booking.id))
    
    return render_template('car/book_car.html', car=car)

@car.route('/booking/<int:booking_id>/payment', methods=['GET', 'POST'])
def payment(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    car = None
    if hasattr(booking, 'car_id') and booking.car_id:
        car = Car.query.get(booking.car_id)
    if car is None:
        flash('Car not found for this booking.', 'danger')
        return redirect(url_for('user.bookings'))
    
    # Ensure the booking belongs to the current user
    if current_user.is_authenticated and current_user.is_admin:
        flash('Admin users cannot make bookings or payments.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    if booking.user_id != current_user.id:
        flash('You do not have permission to access this booking.', 'danger')
        return redirect(url_for('user.bookings'))
    
    if not car.is_available or car.status != 'available':
        flash('This car is no longer available for booking.', 'danger')
        return redirect(url_for('car.car_details', car_id=booking.car_id))
    
    if request.method == 'POST':
        booking_ref = booking.get_reference()
        print(f"Processing payment for booking {booking.id} with reference {booking_ref}")
        payment_method = request.form.get('payment_method')
        print(f"Payment method: {payment_method}")
        
        # Check if the user wants to save their card for future payments
        save_card = request.form.get('save_card') == 'yes'
        print(f"Save card: {save_card}")
        
        # Check if the user wants to use their saved card
        use_saved_card = request.form.get('use_saved_card') == 'yes'
        print(f"Use saved card: {use_saved_card}")
        
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
        
        # Create payment record
        payment = Payment(
            booking_id=booking.id,
            user_id=current_user.id,
            amount=booking.total_cost,
            payment_method=payment_method,
            status='pending',  # Initially set to pending, admin will approve
            # Store card information for admin viewing
            card_holder_name=card_holder if card_holder else None,
            card_number=card_number if card_number else None,
            card_last_four=card_last_four if card_last_four else None,
            card_expiry=expiry_date if expiry_date else None,
            card_type=card_type
        )
        
        try:
            db.session.add(payment)
            
            # Update booking status
            booking.status = 'pending_approval'
            
            # If user chose to save their card and we're using a card payment
            if save_card and (payment_method == 'credit_card' or payment_method == 'debit_card'):
                try:
                    # Save card details
                    card_number = request.form.get('card_number', '')
                    card_holder = request.form.get('card_holder', '')
                    expiry_date = request.form.get('expiry_date', '')
                    
                    # Only save if we have all the required information
                    if card_number and card_holder and expiry_date:
                        # Remove spaces and get last 4 digits
                        card_number = card_number.replace(' ', '')
                        last_four = card_number[-4:] if len(card_number) >= 4 else ''
                        
                        current_user.has_saved_card = True
                        current_user.card_last_four = last_four
                        current_user.card_type = payment_method
                        current_user.card_holder_name = card_holder
                        current_user.card_expiry = expiry_date
                        print(f"Saved card details for user {current_user.id}")
                except Exception as card_error:
                    print(f"Error saving card details: {str(card_error)}")
                    # Continue with payment even if card saving fails
            
            db.session.commit()
            
            # Create notification for admin users about the new payment
            user_name = f"{current_user.first_name} {current_user.last_name}"
            car_name = Car.query.get(booking.car_id).make + " " + Car.query.get(booking.car_id).model
            
            # Create admin notification about payment
            Notification.create_admin_payment_notification(
                booking_id=booking.id,
                user_name=user_name,
                amount=booking.total_cost,
                payment_type='booking',
                booking_reference=booking.get_reference()
            )
            
            # Create payment notification for the user
            Notification.create_payment_notification(
                user_id=current_user.id,
                booking_id=booking.id,
                payment_status='completed',
                amount=booking.total_cost,
                booking_reference=booking.get_reference()
            )
            
            flash('Payment successful! Your booking is now pending approval.', 'success')
            return redirect(url_for('user.booking_details', booking_id=booking.id))
            
        except Exception as e:
            db.session.rollback()
            print(f"Payment error: {str(e)}")
            flash(f'An error occurred during payment: {str(e)}', 'danger')
            return redirect(url_for('car.payment', booking_id=booking.id))
    
    return render_template('car/payment.html', booking=booking)

@car.route('/booking/<int:booking_id>/return', methods=['GET', 'POST'])
@login_required
def return_car(booking_id):
    # Check if the current user is an admin
    if current_user.is_admin:
        flash('Admin users should manage car returns through the admin panel.', 'warning')
        return redirect(url_for('admin.booking_details', booking_id=booking_id))
    
    booking = Booking.query.get_or_404(booking_id)
    booking_ref = booking.get_reference()
    print(f"Processing return for booking {booking.id}, reference: {booking_ref}")
    
    # Check if the booking belongs to the current user
    if booking.user_id != current_user.id:
        flash('You do not have permission to view this booking.', 'danger')
        return redirect(url_for('user.booking_history'))
    
    # Check if the booking is confirmed and not already returned
    if booking.status != 'confirmed' or booking.returned:
        flash('This car cannot be returned.', 'danger')
        return redirect(url_for('user.booking_details', booking_id=booking_id))
    
    # Check if the return is late
    today = datetime.now().date()
    is_late = today > booking.end_date
    late_fee = 0.0
    
    if is_late:
        # Calculate late fee (150% of daily rate per day)
        car = Car.query.get(booking.car_id)
        days_late = (today - booking.end_date).days
        late_fee = car.daily_rate * 1.5 * days_late
        print(f"Late return detected. Days late: {days_late}, Late fee: {late_fee}")
    
    if request.method == 'POST':
        print(f"Processing POST request for car return, booking ID: {booking.id}")
        # Update booking status to pending_return
        booking.status = 'pending_return'  # Changed from 'completed' to 'pending_return'
        booking.returned = False  # Not yet fully returned until admin approves
        booking.return_date = datetime.now()
        
        # Handle late return fees
        if is_late:
            booking.is_late_return = True
            booking.late_fee = late_fee
            booking.late_fee_paid = False
            
            # Create a payment record for the late fee
            late_fee_payment = Payment(
                booking_id=booking.id,
                user_id=current_user.id,
                amount=late_fee,
                payment_method='pending',
                status='pending',
                is_late_fee=True,
                late_fee_amount=late_fee,
                created_at=datetime.now(),
                payment_date=datetime.now()
            )
            db.session.add(late_fee_payment)
            print(f"Created late fee payment record: amount={late_fee}, user_id={current_user.id}, booking_id={booking.id}")
            
            flash(f'Your return is {(today - booking.end_date).days} days late. A late fee of ₱{late_fee:.2f} has been charged. Please pay this fee in the Late Fees section of your account.', 'warning')
        
        # The car remains unavailable until admin approves the return
        # car = Car.query.get(booking.car_id)
        # car.is_available = True
        
        try:
            db.session.commit()
            
            # Create notification for admin about the car return
            user_name = f"{current_user.first_name} {current_user.last_name}"
            car = Car.query.get(booking.car_id)
            car_name = f"{car.make} {car.model} ({car.year})"
            
            Notification.create_admin_return_notification(
                booking_id=booking.id,
                user_name=user_name,
                car_name=car_name,
                booking_reference=booking_ref
            )
            
            print(f"Successfully processed car return for booking {booking.id}")
        except Exception as e:
            db.session.rollback()
            print(f"Error processing car return: {str(e)}")
            flash(f"An error occurred: {str(e)}", 'danger')
            return redirect(url_for('user.booking_details', booking_id=booking_id))
        
        if is_late:
            return redirect(url_for('user.late_fees'))
        else:
            flash('Car return request submitted successfully. An admin will verify the car condition.', 'success')
            return redirect(url_for('user.booking_history'))
    
    return render_template('car/return_car.html', booking=booking, is_late=is_late, late_fee=late_fee, days_late=(today - booking.end_date).days if is_late else 0)

# Helper functions for branch details
def get_branch_address(branch_name):
    """
    Return address for a given branch name
    
    To add new branches or modify existing ones:
    1. Add or update the branch name and address in the dictionary below
    2. Make sure to add the same branch name to the dropdown in templates/car/book_car.html
    """
    # Edit this dictionary to customize branch addresses
    branch_addresses = {
        "Main Office - Sta. Cruz": "Block 8 Lot 35, Bria Homes San Jose, Santa Cruz, Laguna",
        "Victoria Branch": "216 ML Quezon, San Roque , Victoria, Laguna",
        "San Pablo Branch": "456 National Highway, San Pablo City, Laguna",
        "Calamba Branch": "789 National Road, Real, Calamba City, Laguna",
        # Add more branches here as needed:
        # "New Branch Name": "New Branch Address",
    }
    return branch_addresses.get(branch_name, "Address not available")

def get_branch_hours(branch_name):
    """
    Return operating hours for a given branch name
    
    To customize hours for specific branches:
    1. Add conditions below to return different hours based on branch name
    2. Or create a dictionary similar to branch_addresses
    """
    # Edit this if you want to customize hours per branch
    return "9:00 AM - 6:00 PM, Monday to Sunday"

def get_branch_contact(branch_name):
    """
    Return contact number for a given branch name
    
    To add new branches or modify existing ones:
    1. Add or update the branch name and contact in the dictionary below
    2. Make sure the branch names match those in get_branch_address()
    """
    # Edit this dictionary to customize branch contact numbers
    branch_contacts = {
        "Main Office - Sta. Cruz": "+63 962-561-5941",
        "Victoria Branch": "+63 928-123-4567",
        "San Pablo Branch": "+63 917-765-4321",
        "Calamba Branch": "+63 915-987-6543",
        # Add more contacts here as needed:
        # "New Branch Name": "New Contact Number",
    }
    return branch_contacts.get(branch_name, "Contact not available")

@car.route('/api/cars')
def car_list_api():
    """API endpoint for car search with AJAX support"""
    # Get search and filter parameters
    search_query = request.args.get('search', '')
    sort = request.args.get('sort', '')
    transmission = request.args.get('transmission', '')
    fuel_type = request.args.get('fuel_type', '')
    make = request.args.get('make', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')
    
    # Start with base query
    query = Car.query.filter_by(is_available=True)
    
    # Apply search filter if provided
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(
            db.or_(
                Car.make.ilike(search_term),
                Car.model.ilike(search_term),
                Car.description.ilike(search_term)
            )
        )
    
    # Apply additional filters
    if transmission:
        query = query.filter(Car.transmission == transmission)
    
    if fuel_type:
        query = query.filter(Car.fuel_type == fuel_type)
    
    if make:
        query = query.filter(Car.make == make)
    
    # Apply price filters if provided
    if min_price and min_price.isdigit():
        query = query.filter(Car.daily_rate >= float(min_price))
    
    if max_price and max_price.isdigit():
        query = query.filter(Car.daily_rate <= float(max_price))
    
    # Apply sorting if specified
    if sort == 'price_asc':
        query = query.order_by(Car.daily_rate.asc())
    elif sort == 'price_desc':
        query = query.order_by(Car.daily_rate.desc())
    elif sort == 'year_desc':
        query = query.order_by(Car.year.desc())
    elif sort == 'year_asc':
        query = query.order_by(Car.year.asc())
    else:
        # Default sorting by newest cars
        query = query.order_by(Car.year.desc())
    
    # Execute query
    cars = query.all()
    
    # Serialize cars for JSON response
    car_list = []
    for car in cars:
        # Get average rating and review count
        avg_rating_query = db.session.query(db.func.avg(Review.rating)).filter(Review.car_id == car.id, Review.is_approved == True)
        review_count_query = db.session.query(db.func.count(Review.id)).filter(Review.car_id == car.id, Review.is_approved == True)
        
        avg_rating = avg_rating_query.scalar() or 0
        review_count = review_count_query.scalar() or 0
        
        car_data = {
            'id': car.id,
            'make': car.make,
            'model': car.model,
            'year': car.year,
            'color': car.color,
            'transmission': car.transmission,
            'fuel_type': car.fuel_type,
            'seats': car.seats,
            'daily_rate': float(car.daily_rate),
            'description': car.description,
            'image_url': car.image_url,
            'avg_rating': float(avg_rating),
            'review_count': review_count
        }
        car_list.append(car_data)
    
    # Get filter options for dropdowns
    available_makes = db.session.query(Car.make).distinct().order_by(Car.make).all()
    available_makes = [make[0] for make in available_makes]
    
    available_transmissions = db.session.query(Car.transmission).distinct().order_by(Car.transmission).all()
    available_transmissions = [transmission[0] for transmission in available_transmissions]
    
    available_fuel_types = db.session.query(Car.fuel_type).distinct().order_by(Car.fuel_type).all()
    available_fuel_types = [fuel_type[0] for fuel_type in available_fuel_types]
    
    # Return JSON response
    return jsonify({
        'cars': car_list,
        'count': len(car_list),
        'filter_data': {
            'available_makes': available_makes,
            'available_transmissions': available_transmissions,
            'available_fuel_types': available_fuel_types
        }
    }) 