from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify, current_app, abort, make_response
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import calendar
from functools import wraps
from sqlalchemy import func, desc, asc, or_, and_, extract
from sqlalchemy.sql import text
import time
from sqlalchemy.exc import IntegrityError
from models import db
from models.user import User
from models.car import Car
from models.booking import Booking
from models.payment import Payment
from models.review import Review
from models.content import PageContent
from models.loan_car import LoanCar
import uuid
import os
from werkzeug.utils import secure_filename
import json
import locale
import random
import string
import threading

import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

admin = Blueprint('admin', __name__)


# Helper function to convert booking locations JSON to a searchable text format
def booking_to_text(locations_json):
    """Convert booking locations JSON to searchable text for filtering"""
    try:
        if isinstance(locations_json, db.Column):
            # This is for SQL expression context
            return db.func.json_extract(locations_json, '$')
        
        # For Python context (direct data)
        if not locations_json:
            return ""
        
        if isinstance(locations_json, str):
            try:
                locations_data = json.loads(locations_json)
            except:
                return locations_json
        else:
            locations_data = locations_json
        
        if isinstance(locations_data, dict):
            pickup = locations_data.get('pickup', {})
            if isinstance(pickup, dict):
                return pickup.get('name', '')
            return str(pickup)
        
        return str(locations_data)
    except:
        return ""



# Admin middleware to check if user is admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated and admin
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('admin.admin_login'))
        
        # Check for session timeout (30 minutes of inactivity)
        if 'last_activity' in session:
            last_activity = datetime.fromtimestamp(session['last_activity'])
            if (datetime.now() - last_activity).total_seconds() > 1800:  # 30 minutes
                # Log the session timeout
                current_app.logger.warning(f"Admin session timeout for user {current_user.id}")
                
                # Clear session and log out
                session.clear()
                logout_user()
                
                flash('Your session has expired. Please log in again.', 'warning')
                return redirect(url_for('admin.admin_login'))
            
            # Update last activity timestamp
            session['last_activity'] = datetime.now().timestamp()
            session.modified = True
        
        return f(*args, **kwargs)
    return decorated_function


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff', 'svg', 'ico', 'heic', 'heif', 'avif', 'jfif', 'pjpeg', 'pjp'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_image_to_cloudinary(file, folder="car_images"):
    """
    Upload image to Cloudinary and return the secure URL
    """
    if not file or not file.filename:
        return None
        
    if not allowed_file(file.filename):
        flash(f"File type not allowed. Supported formats: {', '.join(ALLOWED_EXTENSIONS)}", 'danger')
        return None
    try:
        # Generate a unique public_id
        filename = secure_filename(file.filename)
        name_without_extension = os.path.splitext(filename)[0]
        
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            file,
            folder=folder,
            public_id=f"{name_without_extension}_{int(time.time())}",
            overwrite=True,
            resource_type="image",
            transformation=[
                {'width': 1000, 'height': 900, 'crop': 'fill', 'quality': 'auto'},
                {'format': 'webp'}  # Convert to WebP for better compression
            ]
        )
        
        return result['secure_url']
        
    except Exception as e:
        print(f"Error uploading image to Cloudinary: {str(e)}")
        flash(f"Error uploading image: {str(e)}", 'danger')
        return None

def delete_image_from_cloudinary(image_url):
    """
    Delete image from Cloudinary using the image URL
    """
    try:
        if not image_url or 'cloudinary.com' not in image_url:
            return True  # Not a Cloudinary URL, nothing to delete
            
        # Extract public_id from URL
        # Example URL: https://res.cloudinary.com/demo/image/upload/v1571218039/sample.jpg
        parts = image_url.split('/')
        if len(parts) >= 2:
            # Get the public_id (filename without extension)
            public_id_with_folder = '/'.join(parts[parts.index('upload')+2:])
            public_id = os.path.splitext(public_id_with_folder)[0]
            
            # Delete from Cloudinary
            result = cloudinary.uploader.destroy(public_id)
            return result.get('result') == 'ok'
    except Exception as e:
        print(f"Error deleting image from Cloudinary: {str(e)}")
        return False
    



@admin.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password) or not user.is_admin:
            flash('Invalid admin credentials.', 'danger')
            return redirect(url_for('admin.admin_login'))
        
        # Login the admin user with remember me option
        login_user(user, remember=True)
        
        # Add session security timestamps and flags
        session.permanent = True
        session['login_timestamp'] = datetime.now().timestamp()
        session['last_activity'] = datetime.now().timestamp()
        session['user_id'] = user.id
        session['is_admin'] = True
        
        # Ensure session data is saved
        session.modified = True
        
        flash('Login successful!', 'success')
        return redirect(url_for('admin.dashboard'))
    
    # Return response with cache control headers
    response = make_response(render_template('admin/auth/login.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@admin.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    # Remove the admin permission check to allow anyone to register as admin
    # admin_exists = User.query.filter_by(is_admin=True).first() is not None
    
    # if admin_exists and (not current_user.is_authenticated or not current_user.is_admin):
    #     flash('You do not have permission to register admin accounts.', 'danger')
    #     return redirect(url_for('admin.admin_login'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        admin_key = request.form.get('admin_key')
        phone_number = request.form.get('phone_number')
        address = request.form.get('address')
        driver_license = request.form.get('driver_license')
        date_of_birth = request.form.get('date_of_birth')
        
        # Validate admin key (you might want to use an environment variable for this)
        if admin_key != "JDM_ADMIN_SECRET_KEY":
            flash('Invalid admin key.', 'danger')
            return redirect(url_for('admin.admin_register'))
        
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('admin.admin_register'))
        
        # Check if user already exists
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists.', 'danger')
            return redirect(url_for('admin.admin_register'))
        
        # Check if email already exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', 'danger')
            return redirect(url_for('admin.admin_register'))
        
        # Process date of birth
        if date_of_birth:
            dob_date = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
        else:
            flash('Date of birth is required.', 'danger')
            return redirect(url_for('admin.admin_register'))
        
        # Create new admin user
        new_admin = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            address=address,
            driver_license=driver_license,
            date_of_birth=dob_date,
            is_admin=True,
            registration_date=datetime.now()
        )
        
        # Add user to database
        db.session.add(new_admin)
        db.session.commit()
        
        flash('Admin registration successful! You can now log in.', 'success')
        return redirect(url_for('admin.admin_login'))
    
    return render_template('admin/auth/register.html', first_admin=False)

@admin.route('/admin/logout', methods=['GET'])
def admin_logout():
    # Store user ID before logout for logging purposes
    user_id = session.get('user_id', 'unknown')
    
    # Log the user out
    logout_user()
    
    # Clear all session data
    session.clear()
    
    # Create response with redirect
    response = make_response(redirect(url_for('admin.admin_login')))
    
    # Set cache control headers
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    # Log the logout action
    current_app.logger.info(f"Admin user {user_id} logged out")
    
    # Add flash message
    flash('You have been logged out successfully.', 'success')
    
    return response

def send_admin_otp_email(to_email, otp):
    """Send OTP to admin's email"""
    try:
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Admin Password Reset OTP</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1a237e; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ padding: 20px; background-color: #f8f9fa; border-radius: 0 0 5px 5px; }}
                .otp-box {{ background-color: #ffffff; padding: 15px; border-radius: 5px; text-align: center; margin: 20px 0; border: 1px solid #dee2e6; }}
                .otp-code {{ font-size: 32px; letter-spacing: 5px; color: #1a237e; font-weight: bold; }}
                .warning {{ color: #dc3545; margin-top: 20px; font-size: 14px; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>JDM Car Rentals - Admin Password Reset</h1>
            </div>
            <div class="content">
                <p>Hello Administrator,</p>
                <p>You have requested to reset your admin password. Please use the following One-Time Password (OTP) to verify your identity:</p>
                
                <div class="otp-box">
                    <div class="otp-code">{otp}</div>
                </div>
                
                <p><strong>Important Security Notice:</strong></p>
                <ul>
                    <li>This OTP will expire in 5 minutes</li>
                    <li>If you did not request this password reset, please contact the system administrator immediately</li>
                    <li>This is for an administrator account - please take extra precautions</li>
                </ul>
                
                <div class="warning">
                    <p>⚠️ Never share this OTP with anyone. The JDM Car Rentals team will never ask for your OTP.</p>
                </div>
            </div>
            <div class="footer">
                <p>This is an automated message from JDM Car Rentals. Please do not reply to this email.</p>
                <p>&copy; {datetime.now().year} JDM Car Rentals. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        # Use the main email sending function
        from email_utils import send_email
        return send_email(to_email, "JDM Car Rentals - Admin Password Reset OTP", html_content)
            
    except Exception as e:
        error_message = str(e)
        print(f"Error sending admin OTP email: {error_message}")
        return False, f"An unexpected error occurred: {error_message}"

@admin.route('/admin/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        
        # Check if admin user exists
        user = User.query.filter_by(email=email, is_admin=True).first()
        if not user:
            flash('No admin account found with that email address.', 'danger')
            return redirect(url_for('admin.forgot_password'))
        
        # Generate 6-digit OTP
        otp = ''.join(random.choices(string.digits, k=6))
        
        # Store OTP in session with expiration time (5 minutes)
        expiry_time = datetime.utcnow() + timedelta(minutes=5)
        session['admin_reset_email'] = email
        session['admin_reset_otp'] = otp
        session['admin_reset_otp_expiry'] = expiry_time.timestamp()
        
        # Send OTP email with better error handling
        success, message = send_admin_otp_email(email, otp)
        if success:
            flash('OTP sent to your email address. Please check your inbox and spam folder.', 'success')
            return redirect(url_for('admin.verify_otp', email=email))
        else:
            if "authorized" in message.lower():
                flash('Your email needs to be authorized in our system first. Please check your inbox for an authorization email from Mailgun or contact support.', 'warning')
            elif "timeout" in message.lower():
                flash('The email service is temporarily unavailable. Please try again in a few minutes.', 'warning')
            elif "connection" in message.lower():
                flash('Unable to connect to the email service. Please try again in a few minutes.', 'warning')
            else:
                flash(f'Error sending OTP: {message}', 'danger')
            return redirect(url_for('admin.forgot_password'))
    
    return render_template('admin/auth/forgot_password.html')

@admin.route('/admin/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    
    email = request.args.get('email') or request.form.get('email')
    
    # Check if we have a reset in progress
    if not email or 'admin_reset_email' not in session or session['admin_reset_email'] != email:
        flash('Password reset session expired or invalid. Please try again.', 'danger')
        return redirect(url_for('admin.forgot_password'))
    
    # Check if OTP has expired
    if 'admin_reset_otp_expiry' in session:
        expiry_time = datetime.fromtimestamp(session['admin_reset_otp_expiry'])
        if datetime.utcnow() > expiry_time:
            # Clear session data
            session.pop('admin_reset_email', None)
            session.pop('admin_reset_otp', None)
            session.pop('admin_reset_otp_expiry', None)
            
            flash('OTP has expired. Please request a new one.', 'danger')
            return redirect(url_for('admin.forgot_password'))
    
    if request.method == 'POST':
        submitted_otp = request.form.get('otp')
        stored_otp = session.get('admin_reset_otp')
        
        if not submitted_otp or submitted_otp != stored_otp:
            flash('Invalid OTP. Please try again.', 'danger')
            return redirect(url_for('admin.verify_otp', email=email))
        
        # Generate a secure token for password reset
        reset_token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        session['admin_reset_token'] = reset_token
        
        return redirect(url_for('admin.reset_password', email=email, token=reset_token))
    
    return render_template('admin/auth/verify_otp.html', email=email)

@admin.route('/admin/reset-password', methods=['GET', 'POST'])
def reset_password():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    
    email = request.args.get('email') or request.form.get('email')
    token = request.args.get('token') or request.form.get('token')
    
    # Validate token and email
    if not email or not token or 'admin_reset_email' not in session or session['admin_reset_email'] != email or 'admin_reset_token' not in session or session['admin_reset_token'] != token:
        flash('Invalid or expired password reset link. Please try again.', 'danger')
        return redirect(url_for('admin.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('admin.reset_password', email=email, token=token))
        
        # Update user's password
        user = User.query.filter_by(email=email, is_admin=True).first()
        if user:
            user.password_hash = generate_password_hash(password)
            db.session.commit()
            
            # Clear session data
            session.pop('admin_reset_email', None)
            session.pop('admin_reset_otp', None)
            session.pop('admin_reset_otp_expiry', None)
            session.pop('admin_reset_token', None)
            
            flash('Your password has been updated successfully! You can now log in with your new password.', 'success')
            return redirect(url_for('admin.admin_login'))
        else:
            flash('Admin user not found.', 'danger')
            return redirect(url_for('admin.forgot_password'))
    
    return render_template('admin/auth/reset_password.html', email=email, token=token)

@admin.route('/admin')
@login_required
@admin_required
def dashboard():
    # Count statistics for dashboard
    user_count = User.query.count()
    car_count = Car.query.count()
    booking_count = Booking.query.count()
    active_bookings = Booking.query.filter(Booking.status == 'confirmed', Booking.returned == False).count()
    
    # Count bookings needing admin approval
    pending_approval_count = Booking.query.filter(Booking.status == 'pending_approval').count()
    
    # Get monthly revenue (use real data from payments)
    current_month = datetime.now().month
    current_year = datetime.now().year
    monthly_revenue_result = db.session.query(db.func.sum(Payment.amount)).filter(
        db.extract('month', Payment.payment_date) == current_month,
        db.extract('year', Payment.payment_date) == current_year,
        Payment.status == 'completed'
    ).scalar()
    monthly_revenue = float(monthly_revenue_result) if monthly_revenue_result is not None else 0.0
    
    # Create stats dictionary
    stats = {
        'total_users': user_count,
        'total_cars': car_count,
        'total_bookings': booking_count,
        'active_bookings': active_bookings,
        'monthly_revenue': monthly_revenue,
        'pending_approval': pending_approval_count
    }
    
    # Get revenue data for the last 6 months
    revenue_data = {'months': [], 'data': []}
    for i in range(5, -1, -1):
        # Calculate month i months ago
        month = current_month - i
        year = current_year
        if month <= 0:
            month += 12
            year -= 1
        
        # Get revenue for this month
        monthly_rev = db.session.query(db.func.sum(Payment.amount)).filter(
            db.extract('month', Payment.payment_date) == month,
            db.extract('year', Payment.payment_date) == year,
            Payment.status == 'completed'
        ).scalar()
        
        monthly_rev = float(monthly_rev) if monthly_rev is not None else 0.0
        
        # Add to data
        month_name = datetime(year, month, 1).strftime('%b')
        revenue_data['months'].append(month_name)
        revenue_data['data'].append(monthly_rev)
    
    # Get popular cars data (based on real booking count)
    popular_cars_query = db.session.query(
        Car.make, Car.model, db.func.count(Booking.id).label('booking_count')
    ).join(Booking).group_by(Car.id).order_by(db.desc('booking_count')).limit(5).all()
    
    popular_cars = {
        'names': [f"{car.make} {car.model}" for car in popular_cars_query],
        'bookings': [car.booking_count for car in popular_cars_query]
    }
    
    # If we don't have enough cars with bookings, fill with empty data
    while len(popular_cars['names']) < 5:
        popular_cars['names'].append("No Data")
        popular_cars['bookings'].append(0)
    
    # Get real system activity
    recent_activities = []
    
    # 1. Recent bookings (last 7 days)
    recent_bookings = Booking.query.filter(
        Booking.booking_date >= datetime.now() - timedelta(days=7)
    ).order_by(Booking.booking_date.desc()).limit(5).all()
    
    for booking in recent_bookings:
        user = User.query.get(booking.user_id)
        car = Car.query.get(booking.car_id)
        if user and car:
            recent_activities.append({
                'description': 'New Booking',
                'details': f"{user.first_name} {user.last_name} booked a {car.make} {car.model} for {booking.duration_days} days",
                'user': user.username,
                'timestamp': booking.booking_date
            })
    
    # 2. Overdue bookings (not returned after end date)
    overdue_bookings = Booking.query.filter(
        Booking.end_date < datetime.now().date(),
        Booking.status == 'confirmed',
        Booking.returned == False
    ).order_by(Booking.end_date).limit(5).all()
    
    for booking in overdue_bookings:
        user = User.query.get(booking.user_id)
        car = Car.query.get(booking.car_id)
        if user and car:
            days_overdue = (datetime.now().date() - booking.end_date).days
            late_fee = booking.calculate_late_fee()
            recent_activities.append({
                'description': 'Overdue Return',
                'details': f"Car {car.make} {car.model} is {days_overdue} days overdue. Late fee: ₱{late_fee}",
                'user': user.username,
                'timestamp': datetime.combine(booking.end_date, datetime.min.time())
            })
    
    # 3. Recent returns (last 7 days)
    recent_returns = Booking.query.filter(
        Booking.return_date >= datetime.now() - timedelta(days=7),
        Booking.returned == True
    ).order_by(Booking.return_date.desc()).limit(5).all()
    
    for booking in recent_returns:
        user = User.query.get(booking.user_id)
        car = Car.query.get(booking.car_id)
        if user and car:
            status = "on time"
            if booking.is_late_return:
                status = f"late (fee: ₱{booking.late_fee})"
                
            recent_activities.append({
                'description': 'Car Return',
                'details': f"{user.first_name} {user.last_name} returned {car.make} {car.model} {status}",
                'user': user.username,
                'timestamp': booking.return_date
            })
    
    # 4. Recent payments (last 7 days)
    recent_payments = Payment.query.filter(
        Payment.payment_date >= datetime.now() - timedelta(days=7),
        Payment.status == 'completed'
    ).order_by(Payment.payment_date.desc()).limit(5).all()
    
    for payment in recent_payments:
        user = User.query.get(payment.user_id)
        if user:
            payment_type = "booking"
            if payment.is_late_fee:
                payment_type = "late fee"
                
            recent_activities.append({
                'description': 'Payment Received',
                'details': f"Payment of ₱{payment.amount} received for {payment_type} from {user.first_name} {user.last_name}",
                'user': user.username,
                'timestamp': payment.payment_date
            })
    
    # Sort all activities by timestamp (most recent first)
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Limit to the 10 most recent activities
    recent_activities = recent_activities[:10]
    
    return render_template('admin/dashboard.html', 
                          stats=stats,
                          revenue_data=revenue_data,
                          popular_cars=popular_cars,
                          recent_activities=recent_activities)

@admin.route('/admin/dashboard/filter', methods=['GET'])
@login_required
@admin_required
def dashboard_filter():
    """API endpoint for filtering dashboard data by time period"""
    period = request.args.get('period', 'month')
    
    # Set date range based on period
    end_date = datetime.now()
    
    if period == 'day':
        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        start_date = end_date - timedelta(days=7)
    elif period == 'month':
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == 'quarter':
        # Find current quarter start date
        current_month = end_date.month
        quarter_start_month = ((current_month - 1) // 3) * 3 + 1
        start_date = end_date.replace(month=quarter_start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == 'year':
        start_date = end_date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        # Default to month
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Get filtered revenue data
    revenue_result = db.session.query(db.func.sum(Payment.amount)).filter(
        Payment.payment_date >= start_date,
        Payment.payment_date <= end_date,
        Payment.status == 'completed'
    ).scalar()
    filtered_revenue = float(revenue_result) if revenue_result is not None else 0.0
    
    # Get filtered booking count
    active_bookings = Booking.query.filter(
        Booking.status == 'confirmed',
        Booking.returned == False,
        Booking.booking_date >= start_date
    ).count()
    
    # Create labels and data for revenue chart based on period
    chart_labels = []
    chart_data = []
    
    if period == 'day':
        # Hourly data for today
        for hour in range(24):
            hour_start = start_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            hour_end = hour_start + timedelta(hours=1)
            
            hour_revenue = db.session.query(db.func.sum(Payment.amount)).filter(
                Payment.payment_date >= hour_start,
                Payment.payment_date < hour_end,
                Payment.status == 'completed'
            ).scalar()
            
            hour_revenue = float(hour_revenue) if hour_revenue is not None else 0.0
            chart_labels.append(f"{hour}:00")
            chart_data.append(hour_revenue)
    
    elif period == 'week':
        # Daily data for past week
        for day in range(7):
            day_date = end_date - timedelta(days=6-day)
            day_start = day_date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            day_revenue = db.session.query(db.func.sum(Payment.amount)).filter(
                Payment.payment_date >= day_start,
                Payment.payment_date < day_end,
                Payment.status == 'completed'
            ).scalar()
            
            day_revenue = float(day_revenue) if day_revenue is not None else 0.0
            chart_labels.append(day_date.strftime("%a"))
            chart_data.append(day_revenue)
    
    elif period in ['month', 'quarter', 'year']:
        # Monthly data
        if period == 'month':
            days_in_month = (end_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            days_in_month = days_in_month.day
            
            for day in range(1, days_in_month + 1):
                day_date = start_date.replace(day=day)
                
                if day_date > end_date:
                    break
                    
                day_start = day_date
                day_end = day_start + timedelta(days=1)
                
                day_revenue = db.session.query(db.func.sum(Payment.amount)).filter(
                    Payment.payment_date >= day_start,
                    Payment.payment_date < day_end,
                    Payment.status == 'completed'
                ).scalar()
                
                day_revenue = float(day_revenue) if day_revenue is not None else 0.0
                chart_labels.append(f"{day}")
                chart_data.append(day_revenue)
        
        else:  # quarter or year
            # Determine number of months to show
            num_months = 3 if period == 'quarter' else 12
            monthly_data = []  # Initialize the monthly_data array
            
            for month_offset in range(num_months):
                if period == 'quarter':
                    month = quarter_start_month + month_offset
                    year = end_date.year
                    if month > 12:
                        month -= 12
                        year += 1
                else:  # year
                    month = month_offset + 1
                    year = end_date.year
                
                # Skip future months
                if year > end_date.year or (year == end_date.year and month > end_date.month):
                    continue
                
                month_start = datetime(year, month, 1)
                if month == 12:
                    month_end = datetime(year + 1, 1, 1)
                else:
                    month_end = datetime(year, month + 1, 1)
                
                month_revenue = db.session.query(db.func.sum(Payment.amount)).filter(
                    Payment.payment_date >= month_start,
                    Payment.payment_date < month_end,
                    Payment.status == 'completed'
                ).scalar() or 0
                
                # Add data to the monthly_data array
                monthly_data.append({
                    'month': month_start.strftime('%b %Y'),
                    'revenue': float(month_revenue)
                })
            
            # Extract the labels and data from monthly_data for the chart
            for item in monthly_data:
                chart_labels.append(item['month'])
                chart_data.append(item['revenue'])
    
    # Return JSON response
    return jsonify({
        'stats': {
            'filtered_revenue': filtered_revenue,
            'active_bookings': active_bookings
        },
        'chart': {
            'labels': chart_labels,
            'data': chart_data
        }
    })

# Car management
@admin.route('/admin/cars')
@login_required
@admin_required
def car_list():
    # Get search and filter parameters
    search_query = request.args.get('search', '')
    make = request.args.get('make', '')
    model = request.args.get('model', '')
    year = request.args.get('year', '')
    availability = request.args.get('availability', '')
    transmission = request.args.get('transmission', '')
    fuel_type = request.args.get('fuel_type', '')
    sort = request.args.get('sort', '')
    
    # Start with base query
    query = Car.query
    
    # Apply search filter if provided
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(
            db.or_(
                Car.make.ilike(search_term),
                Car.model.ilike(search_term),
                Car.license_plate.ilike(search_term),
                Car.description.ilike(search_term)
            )
        )
    
    # Apply additional filters
    if make:
        query = query.filter(Car.make.ilike(f"%{make}%"))
    
    if model:
        query = query.filter(Car.model.ilike(f"%{model}%"))
    
    if year:
        query = query.filter(Car.year == year)
    
    # Replace the availability filtering section with:
    if availability:
        query = query.filter(Car.status == availability)
    
    if transmission:
        query = query.filter(Car.transmission == transmission)
    
    if fuel_type:
        query = query.filter(Car.fuel_type == fuel_type)
    
    # Get all available makes, transmissions, and fuel types for filter dropdowns
    available_makes = db.session.query(Car.make).distinct().order_by(Car.make).all()
    available_makes = [make[0] for make in available_makes]
    
    available_transmissions = db.session.query(Car.transmission).distinct().order_by(Car.transmission).all()
    available_transmissions = [transmission[0] for transmission in available_transmissions]
    
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
    elif sort == 'id_asc':
        query = query.order_by(Car.id.asc())
    elif sort == 'id_desc':
        query = query.order_by(Car.id.desc())
    else:
        # Default sorting by ID (descending)
        query = query.order_by(Car.id.desc())
    
    # Execute query
    cars = query.all()

    return render_template('admin/cars/list.html', 
                          cars=cars, 
                          search_query=search_query,
                          current_sort=sort,
                          available_makes=available_makes,
                          available_transmissions=available_transmissions,
                          available_fuel_types=available_fuel_types)


@admin.route('/admin/cars/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_car():
    if request.method == 'POST':
        # Get form data
        make = request.form.get('make')
        model = request.form.get('model')
        year = request.form.get('year')
        color = request.form.get('color')
        license_plate = request.form.get('license_plate')
        vin = request.form.get('vin')
        daily_rate = request.form.get('daily_rate')
        transmission = request.form.get('transmission')
        fuel_type = request.form.get('fuel_type')
        seats = request.form.get('seats')
        description = request.form.get('description')
        horsepower = request.form.get('horsepower')
        mileage = request.form.get('mileage')
        body_type = request.form.get('body_type')
        image_url = request.form.get('image_url')
        status = request.form.get('status', 'available') 
        
        # Validate fields
        errors = []
        
        # VIN validation
        if not vin:
            errors.append('VIN is required')
        elif len(vin) != 17:
            errors.append('VIN must be exactly 17 characters')
        elif any(c in vin.upper() for c in 'IOQ'):
            errors.append('VIN cannot contain the letters I, O, or Q')
            
        # Basic validation for other fields
        if not make or len(make) > 50:
            errors.append('Make is required and must be less than 50 characters')
            
        if not model or len(model) > 50:
            errors.append('Model is required and must be less than 50 characters')
            
        if not license_plate or len(license_plate) > 20:
            errors.append('License plate is required and must be less than 20 characters')
            
        # If there are validation errors, flash them and return to form
        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('admin.add_car'))
        
        # Handle image upload to Cloudinary
        if 'car_image' in request.files:
            file = request.files['car_image']
            if file and file.filename:  # Check if a file was actually selected
                cloudinary_url = upload_image_to_cloudinary(file)
                if cloudinary_url:
                    image_url = cloudinary_url  # Use Cloudinary URL
                elif file.filename:  # If file was selected but upload failed
                    return redirect(url_for('admin.add_car'))
        
        # Check if license plate or VIN already exists
        existing_car = Car.query.filter((Car.license_plate == license_plate) | (Car.vin == vin)).first()
        if existing_car:
            flash('A car with this license plate or VIN already exists.', 'danger')
            return redirect(url_for('admin.add_car'))
        
        # Create new car
        try:
            new_car = Car(
                make=make,
                model=model,
                year=year,
                color=color,
                license_plate=license_plate,
                vin=vin,
                daily_rate=daily_rate,
                transmission=transmission,
                fuel_type=fuel_type,
                seats=seats,
                description=description,
                horsepower=horsepower,
                mileage=mileage,
                body_type=body_type,
                image_url=image_url,  # Store Cloudinary URL in database
                is_available=(status == 'available'),  # Default availability
                status='available'  # Default status
            )
            
            db.session.add(new_car)
            db.session.commit()
            
            flash('Car added successfully!', 'success')
            return redirect(url_for('admin.car_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding car: {str(e)}', 'danger')
            return redirect(url_for('admin.add_car'))
    
    return render_template('admin/cars/add.html')

@admin.route('/admin/cars/<int:car_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_car(car_id):
    car = Car.query.get_or_404(car_id)

    if request.method == 'POST':
        # Get form data
        make = request.form.get('make')
        model = request.form.get('model')
        year = request.form.get('year')
        color = request.form.get('color')
        license_plate = request.form.get('license_plate')
        vin = request.form.get('vin')
        daily_rate = request.form.get('daily_rate')
        transmission = request.form.get('transmission')
        fuel_type = request.form.get('fuel_type')
        seats = request.form.get('seats')
        description = request.form.get('description')
        horsepower = request.form.get('horsepower')
        mileage = request.form.get('mileage')
        body_type = request.form.get('body_type')
        status = request.form.get('status')
        image_url = request.form.get('image_url')

        errors = []

        # VIN validation
        if not vin:
            errors.append('VIN is required')
        elif len(vin) != 17:
            errors.append('VIN must be exactly 17 characters')
        elif any(c in vin.upper() for c in 'IOQ'):
            errors.append('VIN cannot contain the letters I, O, or Q')

        if not make or len(make) > 50:
            errors.append('Make is required and must be less than 50 characters')

        if not model or len(model) > 50:
            errors.append('Model is required and must be less than 50 characters')

        if not license_plate or len(license_plate) > 20:
            errors.append('License plate is required and must be less than 20 characters')

        # Check for duplicates
        existing_car = Car.query.filter(
            ((Car.license_plate == license_plate) | (Car.vin == vin)) &
            (Car.id != car_id)
        ).first()

        if existing_car:
            errors.append('Another car with this license plate or VIN already exists')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('admin.edit_car', car_id=car_id))

        try:
            # Check if car is in active loan
            active_loan_offers = LoanCar.query.filter(
                LoanCar.car_id == car_id,
                LoanCar.status.in_(['available', 'pending', 'active'])
            ).first()

            if active_loan_offers:
                flash('Cannot edit car that is currently offered for loan.', 'danger')
                return redirect(url_for('admin.edit_car', car_id=car_id))

            if car.status == 'sold':
                flash('Cannot edit the car. Already sold for loan.', 'danger')
                return redirect(url_for('admin.edit_car', car_id=car_id))

            # Save old image before possible overwrite
            old_image_url = car.image_url

            # Update car fields
            car.make = make
            car.model = model
            car.year = year
            car.color = color
            car.license_plate = license_plate
            car.vin = vin
            car.daily_rate = daily_rate
            car.transmission = transmission
            car.fuel_type = fuel_type
            car.seats = seats
            car.description = description
            car.body_type = body_type
            car.status = status
            car.is_available = (status == 'available')

            if horsepower:
                car.horsepower = int(horsepower)
            if mileage:
                car.mileage = int(mileage)

            # If status is available, cancel related bookings
            if car.status == 'available':
                Booking.query.filter_by(car_id=car.id, status='booked').update({'status': 'cancelled'})

            # If status is offered_for_loan, update related loan offer
            if car.status == 'offered_for_loan':
                loan_offer = LoanCar.query.filter_by(car_id=car.id).first()
                if loan_offer:
                    loan_offer.status = 'available'

            # Handle image upload
            new_image_uploaded = False
            if 'car_image' in request.files:
                file = request.files['car_image']
                if file and file.filename:
                    cloudinary_url = upload_image_to_cloudinary(file)
                    if cloudinary_url:
                        image_url = cloudinary_url
                        new_image_uploaded = True
                    else:
                        flash('Image upload failed.', 'danger')
                        return redirect(url_for('admin.edit_car', car_id=car_id))

            if image_url and image_url.strip():
                car.image_url = image_url
                if new_image_uploaded and old_image_url and old_image_url != image_url:
                    delete_image_from_cloudinary(old_image_url)

            db.session.commit()
            flash('Car updated successfully!', 'success')
            return redirect(url_for('admin.car_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating car: {str(e)}', 'danger')
            return redirect(url_for('admin.edit_car', car_id=car_id))

    return render_template('admin/cars/edit.html', car=car)

@admin.route('/admin/cars/<int:car_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_car(car_id):
    car = Car.query.get_or_404(car_id)
    image_url = car.image_url  # Store image URL for potential deletion
    
    try:
        # Check if the car is currently offered on loan
        active_loan_offers = LoanCar.query.filter(
            LoanCar.car_id == car_id,
            LoanCar.status == 'active'  # Based on your loan car system
        ).first()
        
        if active_loan_offers:
            flash('Cannot delete car that is currently active for loan.', 'danger')
            return redirect(url_for('admin.car_list'))
        
        pending_loan_offer = LoanCar.query.filter(
            LoanCar.car_id == car_id,
            LoanCar.status == 'pending'
        ).first()
        

        if(pending_loan_offer):
            flash('Cannot delete car that is currently offered for loan. Please withdraw the offer first before deleting this car.', 'danger')
            return redirect(url_for('admin.car_list'))
        
        active_bookings = Booking.query.filter(
            Booking.car_id == car_id,
            Booking.status.in_(['pending', 'confirmed']),
            Booking.returned == False
        ).first()
        
        
        
        if active_bookings:
            flash('Cannot delete car with active bookings.', 'danger')
            return redirect(url_for('admin.car_list'))
        
        # If no active loans or bookings, proceed with deletion
        # Delete completed/inactive loan records
        LoanCar.query.filter_by(car_id=car_id).delete()
        
        # Find all bookings associated with this car
        related_bookings = Booking.query.filter_by(car_id=car_id).all()
        
        # Delete in proper order to avoid foreign key constraint errors
        for booking in related_bookings:
            # First, delete reviews associated with this booking
            reviews = Review.query.filter_by(booking_id=booking.id).all()
            for review in reviews:
                db.session.delete(review)
                
            # Then delete payments associated with this booking
            payments = Payment.query.filter_by(booking_id=booking.id).all()
            for payment in payments:
                db.session.delete(payment)
        
        # Delete any direct reviews associated with this car
        direct_reviews = Review.query.filter_by(car_id=car_id).all()
        for review in direct_reviews:
            db.session.delete(review)
        
        # Delete the bookings
        for booking in related_bookings:
            db.session.delete(booking)
        
        # Finally delete the car
        db.session.delete(car)
        
        # Commit all changes
        db.session.commit()
        
        # Delete image from Cloudinary after successful database deletion
        if image_url:
            try:
                delete_image_from_cloudinary(image_url)
            except Exception as img_error:
                # Log the error but don't fail the deletion
                print(f"Warning: Could not delete image from Cloudinary: {img_error}")
        
        flash('Car deleted successfully!', 'success')
        return redirect(url_for('admin.car_list'))
        
    except IntegrityError as e:
        db.session.rollback()
        print(f"Integrity Error: {e}")
        flash('Cannot delete car due to database constraints. Please contact support.', 'danger')
        return redirect(url_for('admin.car_list'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Unexpected error during car deletion: {e}")
        flash('An unexpected error occurred while deleting the car. Please try again.', 'danger')
        return redirect(url_for('admin.car_list'))

@admin.route('/api/admin/cars')
@login_required
@admin_required
def car_list_api():
    # Get search and filter parameters
    search_query = request.args.get('search', '')
    make = request.args.get('make', '')
    model = request.args.get('model', '')
    year = request.args.get('year', '')
    availability = request.args.get('availability', '')
    transmission = request.args.get('transmission', '')
    fuel_type = request.args.get('fuel_type', '')
    sort = request.args.get('sort', '')
    
    # Start with base query
    query = Car.query
    
    # Apply search filter if provided
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(
            db.or_(
                Car.make.ilike(search_term),
                Car.model.ilike(search_term),
                Car.license_plate.ilike(search_term),
                Car.description.ilike(search_term)
            )
        )
    
    # Apply additional filters
    if make:
        query = query.filter(Car.make.ilike(f"%{make}%"))
    
    if model:
        query = query.filter(Car.model.ilike(f"%{model}%"))
    
    if year:
        query = query.filter(Car.year == year)
    
    if availability == 'available':
        query = query.filter(
            (Car.status == 'available') & 
            (Car.is_available == True)
        )
    elif availability == 'rented':
        query = query.filter(Car.status == 'rented')
    elif availability == 'maintenance':
        query = query.filter(Car.status == 'maintenance')
    elif availability == 'offered_for_loan':
        query = query.filter(Car.status == 'offered_for_loan')
    
    if transmission:
        query = query.filter(Car.transmission == transmission)
    
    if fuel_type:
        query = query.filter(Car.fuel_type == fuel_type)
    
    # Apply sorting if specified
    if sort == 'price_asc':
        query = query.order_by(Car.daily_rate.asc())
    elif sort == 'price_desc':
        query = query.order_by(Car.daily_rate.desc())
    elif sort == 'year_desc':
        query = query.order_by(Car.year.desc())
    elif sort == 'year_asc':
        query = query.order_by(Car.year.asc())
    elif sort == 'id_asc':
        query = query.order_by(Car.id.asc())
    elif sort == 'id_desc':
        query = query.order_by(Car.id.desc())
    else:
        # Default sorting by ID (descending)
        query = query.order_by(Car.id.desc())
    
    # Execute query and serialize the results
    cars = query.all()
    car_list = [{
        'id': car.id,
        'make': car.make,
        'model': car.model,
        'year': car.year,
        'color': car.color,
        'license_plate': car.license_plate,
        'daily_rate': float(car.daily_rate),
        'transmission': car.transmission,
        'fuel_type': car.fuel_type,
        'seats': car.seats,
        'image_url': car.image_url,
        'is_available': car.is_available,
        'status': car.status
    } for car in cars]
    
    # Get all available makes, transmissions, and fuel types for filter dropdowns
    available_makes = db.session.query(Car.make).distinct().order_by(Car.make).all()
    available_makes = [make[0] for make in available_makes]
    
    available_transmissions = db.session.query(Car.transmission).distinct().order_by(Car.transmission).all()
    available_transmissions = [transmission[0] for transmission in available_transmissions]
    
    available_fuel_types = db.session.query(Car.fuel_type).distinct().order_by(Car.fuel_type).all()
    available_fuel_types = [fuel_type[0] for fuel_type in available_fuel_types]
    
    return jsonify({
        'cars': car_list,
        'count': len(car_list),
        'filter_data': {
            'available_makes': available_makes,
            'available_transmissions': available_transmissions,
            'available_fuel_types': available_fuel_types
        }
    })

# User management
@admin.route('/admin/users', methods=['GET', 'POST'])
@login_required
@admin_required
def user_list():
    # Handle form submission for adding a new user
    if request.method == 'POST' and request.form.get('action') == 'add_user':
        # Get form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        address = request.form.get('address')
        date_of_birth = request.form.get('date_of_birth')
        driver_license = request.form.get('driver_license')
        role = request.form.get('role')
        is_active = 'is_active' in request.form
        
        # Validate required fields
        if not (first_name and last_name and email and password):
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('admin.user_list'))
            
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('A user with that email already exists', 'danger')
            return redirect(url_for('admin.user_list'))
            
        # Create username from email
        username = email.split('@')[0]
        
        # Generate hashed password
        password_hash = generate_password_hash(password)
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone,
            address=address,
            is_admin=(role == 'admin'),
            is_active=is_active
        )
        
        # Handle date of birth if provided
        if date_of_birth:
            new_user.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d')
            
        # Set driver's license if provided
        if driver_license:
            new_user.driver_license = driver_license
        else:
            new_user.driver_license = "Not provided"
        
        # Save to database
        db.session.add(new_user)
        db.session.commit()
        
        flash('User created successfully!', 'success')
        return redirect(url_for('admin.user_list'))
    
    # For GET requests, handle filtering and search
    search_query = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    sort = request.args.get('sort', 'id_desc')
    
    # Start with base query
    query = User.query
    
    # Apply search filter
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(
            db.or_(
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term),
                User.email.ilike(search_term),
                User.username.ilike(search_term),
                User.phone_number.ilike(search_term)
            )
        )
    
    # Apply role filter
    if role_filter == 'admin':
        query = query.filter(User.is_admin == True)
    elif role_filter == 'user':
        query = query.filter(User.is_admin == False)
    
    # Apply status filter
    if status_filter == 'active':
        query = query.filter(User.is_active == True)
    elif status_filter == 'inactive':
        query = query.filter(User.is_active == False)
    
    # Apply sorting
    if sort == 'name_asc':
        query = query.order_by(User.first_name.asc(), User.last_name.asc())
    elif sort == 'name_desc':
        query = query.order_by(User.first_name.desc(), User.last_name.desc())
    elif sort == 'email_asc':
        query = query.order_by(User.email.asc())
    elif sort == 'email_desc':
        query = query.order_by(User.email.desc())
    elif sort == 'date_asc':
        query = query.order_by(User.registration_date.asc())
    elif sort == 'date_desc':
        query = query.order_by(User.registration_date.desc())
    elif sort == 'id_asc':
        query = query.order_by(User.id.asc())
    else:  # Default to id_desc
        query = query.order_by(User.id.desc())
    
    # Execute query
    users = query.all()
    
    return render_template('admin/user_management.html', 
                          users=users, 
                          search_query=search_query,
                          current_sort=sort)

@admin.route('/admin/users/<int:user_id>')
@login_required
@admin_required
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    bookings = Booking.query.filter_by(user_id=user_id).all()
    
    return render_template('admin/user_details.html', user=user, bookings=bookings)

@admin.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # Update user details
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.phone_number = request.form.get('phone_number')
        user.address = request.form.get('address')
        user.driver_license = request.form.get('driver_license')
        
        # Only update password if provided
        new_password = request.form.get('password')
        if new_password and new_password.strip():
            user.password_hash = generate_password_hash(new_password)
        
        # Handle admin status
        is_admin = request.form.get('is_admin') == 'True'
        is_active = request.form.get('is_active') == 'True'
        
        # Only allow admin status change if the current user is an admin
        if current_user.is_admin:
            user.is_admin = is_admin
            user.is_active = is_active
        
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.user_list'))
    
    return render_template('admin/edit_user.html', user=user)

@admin.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Don't allow deleting admin users
    if user.is_admin:
        flash('Cannot delete admin users.', 'danger')
        return redirect(url_for('admin.user_list'))
    
    try:
        # First, delete all notifications associated with the user
        from models.notification import Notification
        notifications = Notification.query.filter_by(user_id=user_id).all()
        for notification in notifications:
            db.session.delete(notification)
        
        # Delete all payments associated with the user's bookings
        bookings = Booking.query.filter_by(user_id=user_id).all()
        for booking in bookings:
            # Delete payments for this booking
            payments = Payment.query.filter_by(booking_id=booking.id).all()
            for payment in payments:
                db.session.delete(payment)
        
        # Delete any direct payments associated with the user
        direct_payments = Payment.query.filter_by(user_id=user_id).all()
        for payment in direct_payments:
            db.session.delete(payment)
        
        # Delete associated reviews
        reviews = Review.query.filter_by(user_id=user_id).all()
        for review in reviews:
            db.session.delete(review)
        
        # Delete associated bookings
        for booking in bookings:
            db.session.delete(booking)
        
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        
        flash('User and associated data deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')
    
    return redirect(url_for('admin.user_list'))

# Booking management
@admin.route('/admin/bookings')
@login_required
@admin_required
def booking_list():
    booking_id = request.args.get('booking_id', '')
    user_id = request.args.get('user_id', '')
    status = request.args.get('status', '')
    date_range = request.args.get('date_range', '')
    location = request.args.get('location', '')
    

    query = Booking.query

    if booking_id:
        query = query.filter(Booking.id == booking_id)

    if user_id:
        query = query.filter(Booking.user_id == user_id)

    if status:
        query = query.filter(Booking.status == status)

    # Date range filters
    if date_range:
        today = datetime.now().date()
        if date_range == 'today':
            # Today's bookings
            query = query.filter(func.date(Booking.booking_date) == today)
        elif date_range == 'week':
            # This week's bookings
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            query = query.filter(
                func.date(Booking.booking_date) >= start_of_week,
                func.date(Booking.booking_date) <= end_of_week
            )
        elif date_range == 'month':
            # This month's bookings
            start_of_month = today.replace(day=1)
            last_day = calendar.monthrange(today.year, today.month)[1]
            end_of_month = today.replace(day=last_day)
            query = query.filter(
                func.date(Booking.booking_date) >= start_of_month,
                func.date(Booking.booking_date) <= end_of_month
            )

    # Location filter using JSON operators
    if location:
        # Build a collection of conditions to handle various location storage formats
        location_conditions = [
            # Standard JSON path for pickup.name
            db.cast(db.func.json_extract(Booking.locations, '$.pickup.name'), db.String) == location,
            # Direct string search in the JSON
            Booking.locations.cast(db.String).like(f'%"{location}"%')
        ]
        
        # Create the combined filter
        query = query.filter(db.or_(*location_conditions))

    # Get all bookings after applying filters
    bookings = query.all()

    # Join with users and cars
    for booking in bookings:
        booking.user = User.query.get(booking.user_id)
        if booking.car_id:
            booking.car = Car.query.get(booking.car_id)
        else:
            booking.car = None

    return render_template('admin/bookings/list.html', bookings=bookings)

@admin.route('/admin/bookings/<int:booking_id>')
@login_required
@admin_required
def booking_details(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    return render_template('admin/bookings/details.html', booking=booking)

@admin.route('/admin/bookings/<int:booking_id>/update-status', methods=['POST'])
@login_required
@admin_required
def update_booking_status(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    status = request.form.get('status')
    car = Car.query.get(booking.car_id)
    print(f"Updating booking #{booking_id} status to {status}")
    
    if car.status == 'offered_for_loan':
        flash('Cannot update booking status for a car that is currently offered for loan. Please withdraw the offer first.', 'danger')
        return redirect(url_for('admin.booking_details', booking_id=booking_id))
    
    if status in ['pending', 'pending_approval', 'confirmed', 'pending_return', 'completed', 'cancelled']:
        old_status = booking.status
        booking.status = status
        
        # Update car availability based on status change
        car = Car.query.get(booking.car_id)
        
        # If status is changed to confirmed, make car unavailable
        if status == 'confirmed' and old_status != 'confirmed':
            car.is_available = False
            
            # Start a new thread for sending the confirmation email
            def send_email_thread():
                try:
                    print(f"Sending confirmation email for booking {booking.id} to user {booking.user_id}")
                    email_sent = send_booking_confirmation_email(booking)
                    if not email_sent:
                        print(f"Failed to send confirmation email for booking {booking.id}")
                except Exception as e:
                    print(f"Exception during email sending: {str(e)}")
            
            # Start the email thread
            email_thread = threading.Thread(target=send_email_thread)
            email_thread.start()
            
            # If this booking has a payment, mark it as completed if it's pending
            if booking.payment and booking.payment.status == 'pending':
                booking.payment.status = 'completed'
                print(f"Automatically marking payment #{booking.payment.id} as completed")
            
            flash('Booking confirmed! The car has been marked as unavailable. A confirmation email is being sent to the user.', 'success')
        
        # If status is pending_approval, it's awaiting admin review after payment
        elif status == 'pending_approval':
            flash('Booking marked as pending approval. Please review payment details.', 'info')
            car.status = 'pending_booking'
        
        # If status is pending_return, the customer is trying to return the car
        elif status == 'pending_return':
            flash('Booking marked as pending return. Please inspect the car and approve or reject the return.', 'info')
            car.status = 'pending_return'
        
        # If status is cancelled, make car available again
        elif status == 'cancelled':
            car.status = 'available'
            car.is_available = True
            flash('Booking cancelled! The car has been marked as available.', 'success')
        
        # If status is completed from pending_return, approve the return
        elif status == 'completed' and old_status == 'pending_return':
            car.status = 'available'
            car.is_available = True
            booking.returned = True
            if not booking.return_date:
                booking.return_date = datetime.utcnow()
            flash('Return approved! The car has been marked as returned and available for new bookings.', 'success')
            
            # Create notification for the user that their return was approved
            user = User.query.get(booking.user_id)
            from models.notification import Notification
            
            Notification(
                user_id=booking.user_id,
                booking_id=booking.id,
                title='Car Return Approved',
                message=f'Your car return for booking #{booking.get_reference()} has been approved. Thank you for choosing JDM Car Rentals!',
                notification_type='booking_status',
                is_read=False
            )
        
        # If status is completed from another status, make car available again
        elif status == 'completed' and not booking.returned:
            car.is_available = True
            booking.returned = True
            booking.return_date = datetime.utcnow()
            flash('Booking completed! The car has been marked as returned and available.', 'success')
        else:
            flash('Booking status updated successfully!', 'success')
        
        try:
            # Create notification for the user about the status change
            from models.notification import Notification
            # Only create notification if status has actually changed
            if old_status != status:
                Notification.create_booking_notification(
                    user_id=booking.user_id,
                    booking_id=booking.id,
                    booking_status=status,
                    booking_reference=booking.get_reference()
                )
                print(f"Created notification for user {booking.user_id} about booking status change to {status}")
            
            if booking.status == 'confirmed':
                car.status = 'rented'
                car.is_available = False
            
            elif booking.status in ['pending', 'pending_approval']:
                car.status = 'pending_booking'
                car.is_available = False
                
            db.session.commit()
            print(f"Successfully updated booking #{booking_id} status to {status}")
        except Exception as db_error:
            db.session.rollback()
            print(f"Database error: {str(db_error)}")
            flash(f'An error occurred: {str(db_error)}', 'danger')
    else:
        flash('Invalid status.', 'danger')
    
    return redirect(url_for('admin.booking_details', booking_id=booking_id))

def send_booking_confirmation_email(booking):
    """Send booking confirmation email to user when booking is confirmed by admin"""
    try:
        print(f"Attempting to send confirmation email for booking {booking.id}")
        
        # Get user and car details
        user = User.query.get(booking.user_id)
        car = Car.query.get(booking.car_id)
        
        if not user or not car:
            print(f"Error: User or car not found for booking {booking.id}")
            return False
        
        # Check if user has a valid email
        if not user.email or '@' not in user.email:
            print(f"Error: User {user.id} has invalid email: {user.email}")
            return False
            
        to_email = user.email
        print(f"Sending confirmation email to: {to_email}")
        subject = "JDM Car Rentals - Your Booking Has Been Confirmed"
        
        # Create a more visually appealing HTML email template
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Booking Confirmation</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1a237e; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .details {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .details table {{ width: 100%; border-collapse: collapse; }}
                .details td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
                .details tr:last-child td {{ border-bottom: none; }}
                .footer {{ background-color: #f5f5f5; padding: 15px; text-align: center; font-size: 12px; margin-top: 20px; }}
                .button {{ display: inline-block; background-color: #1a237e; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Booking Confirmation</h1>
            </div>
            <div class="content">
                <p>Dear {user.first_name} {user.last_name},</p>
                <p>Great news! Your car rental booking has been confirmed by our admin team.</p>
                
                <div class="details">
                    <h3>Booking Details:</h3>
                    <table>
                        <tr>
                            <td><strong>Booking ID:</strong></td>
                            <td>{booking.id}</td>
                        </tr>
                        <tr>
                            <td><strong>Booking Reference:</strong></td>
                            <td>{booking.get_reference()}</td>
                        </tr>
                        <tr>
                            <td><strong>Car:</strong></td>
                            <td>{car.make} {car.model} ({car.year})</td>
                        </tr>
                        <tr>
                            <td><strong>Pickup Date:</strong></td>
                            <td>{booking.start_date.strftime('%B %d, %Y')}</td>
                        </tr>
                        <tr>
                            <td><strong>Return Date:</strong></td>
                            <td>{booking.end_date.strftime('%B %d, %Y')}</td>
                        </tr>
                        <tr>
                            <td><strong>Total Cost:</strong></td>
                            <td>₱{booking.total_cost:.2f}</td>
                        </tr>
                        <tr>
                            <td><strong>Status:</strong></td>
                            <td>Confirmed</td>
                        </tr>
                    </table>
                </div>
                
                <p>You can view your booking details anytime by logging into your account.</p>
                <p>If you have any questions, please don't hesitate to contact our customer support.</p>
                
                <p>Thank you for choosing JDM Car Rentals!</p>
                <p>Best regards,<br>JDM Car Rentals Team</p>
            </div>
            <div class="footer">
                <p>This is an automated message. Please do not reply to this email.</p>
                <p>&copy; 2023 JDM Car Rentals. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        # Import the email function from app
        from app import send_email
        
        # Send email and return the result
        print("Sending booking confirmation email...")
        result = send_email(to_email, subject, html_content)
        
        if result:
            print(f"Email successfully sent to {to_email}")
            return True
        else:
            print(f"Failed to send email to {to_email}. This might be because the email address is not authorized in the Mailgun sandbox domain.")
            return False
            
    except Exception as e:
        print(f"Error sending booking confirmation email: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

@admin.route('/admin/bookings/<int:booking_id>/send-confirmation', methods=['GET'])
@login_required
@admin_required
def send_booking_confirmation(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Only allow sending confirmation emails for confirmed bookings
    if booking.status != 'confirmed':
        flash('Confirmation emails can only be sent for confirmed bookings.', 'warning')
        return redirect(url_for('admin.booking_details', booking_id=booking_id))
    
    # Send the confirmation email
    print(f"Admin manually initiating confirmation email for booking {booking_id}")
    if send_booking_confirmation_email(booking):
        flash('Confirmation email sent successfully!', 'success')
    else:
        flash('Failed to send confirmation email. Please check the console logs for more details.', 'danger')
    
    return redirect(url_for('admin.booking_details', booking_id=booking_id))

# Review management
@admin.route('/admin/reviews')
@login_required
@admin_required
def review_list():
    # Get filter parameters
    status = request.args.get('status')
    rating = request.args.get('rating')
    car_id = request.args.get('car_id')
    
    # Start with base query
    query = Review.query
    
    # Apply filters
    if status:
        if status == 'approved':
            query = query.filter(Review.is_approved == True)
        elif status == 'pending':
            query = query.filter(Review.is_approved == False)
    
    if rating:
        query = query.filter(Review.rating >= int(rating))
    
    if car_id:
        query = query.filter(Review.car_id == int(car_id))
    
    # Get final results
    reviews = query.order_by(Review.review_date.desc()).all()
    
    # Calculate stats for the dashboard
    total_reviews = Review.query.count()
    approved_reviews = Review.query.filter(Review.is_approved == True).count()
    pending_reviews = Review.query.filter(Review.is_approved == False).count()
    
    stats = {
        'total': total_reviews,
        'approved': approved_reviews,
        'pending': pending_reviews
    }
    
    return render_template('admin/reviews/list.html', reviews=reviews, stats=stats)

@admin.route('/admin/reviews/<int:review_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_review(review_id):
    review = Review.query.get_or_404(review_id)
    review.is_approved = True
    db.session.commit()
    
    flash('Review approved successfully!', 'success')
    return redirect(url_for('admin.review_list'))

@admin.route('/admin/reviews/<int:review_id>/disapprove', methods=['POST'])
@login_required
@admin_required
def disapprove_review(review_id):
    review = Review.query.get_or_404(review_id)
    review.is_approved = False
    db.session.commit()
    
    flash('Review disapproved successfully!', 'success')
    return redirect(url_for('admin.review_list'))

@admin.route('/admin/reviews/<int:review_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    
    flash('Review deleted successfully!', 'success')
    return redirect(url_for('admin.review_list'))

@admin.route('/admin/payments')
@login_required
@admin_required
def payment_list():
    # Get filter parameters
    payment_type = request.args.get('type', '')
    status = request.args.get('status', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    search = request.args.get('search', '')
    
    # Date ranges for template
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    first_day_of_month = datetime(now.year, now.month, 1).strftime('%Y-%m-%d')
    first_day_of_year = datetime(now.year, 1, 1).strftime('%Y-%m-%d')
    one_week_ago = (now - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # Formatted links for date filters
    date_filters = {
        'today': url_for('admin.payment_list', start_date=today, end_date=today),
        'week': url_for('admin.payment_list', start_date=one_week_ago, end_date=today),
        'month': url_for('admin.payment_list', start_date=first_day_of_month, end_date=today),
        'year': url_for('admin.payment_list', start_date=first_day_of_year, end_date=today)
    }
    
    # Start with base query
    query = Payment.query
    
    # Apply filters
    if payment_type == 'booking':
        query = query.filter(Payment.is_late_fee == False)
    elif payment_type == 'late_fee':
        query = query.filter(Payment.is_late_fee == True)
        
    if status:
        query = query.filter(Payment.status == status)
        
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Payment.payment_date >= start_date_obj)
        except ValueError:
            flash('Invalid start date format. Please use YYYY-MM-DD.', 'warning')
            
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            # Add one day to include the end date fully
            end_date_obj = end_date_obj + timedelta(days=1)
            query = query.filter(Payment.payment_date < end_date_obj)
        except ValueError:
            flash('Invalid end date format. Please use YYYY-MM-DD.', 'warning')
            
    if search:
        # Join with User and Booking to allow searching by user name or booking reference
        query = query.join(User, Payment.user_id == User.id)
        query = query.outerjoin(Booking, Payment.booking_id == Booking.id)
        
        # Apply search filters
        search_term = f"%{search}%"
        or_conditions = [
            Payment.payment_method.ilike(search_term),
            User.username.ilike(search_term),
            User.email.ilike(search_term),
            # Only include booking_reference if it exists in the Booking model
            Booking.booking_reference.ilike(search_term) if hasattr(Booking, 'booking_reference') else False,
            # Add other conditions as needed
        ]
        query = query.filter(
            db.or_(
                *or_conditions
            )
        )
    
    # Get payment statistics
    total_payments = Payment.query.count()
    total_revenue = db.session.query(db.func.sum(Payment.amount)).filter(Payment.status == 'completed').scalar() or 0
    total_pending = db.session.query(db.func.sum(Payment.amount)).filter(Payment.status == 'pending').scalar() or 0
    
    # Get payment method statistics
    payment_methods = db.session.query(
        Payment.payment_method, 
        db.func.count(Payment.id).label('count'),
        db.func.sum(Payment.amount).label('total')
    ).filter(Payment.status == 'completed').group_by(Payment.payment_method).all()
    
    # Get today's payments
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    today_payments = Payment.query.filter(
        Payment.payment_date >= today,
        Payment.payment_date < tomorrow,
        Payment.status == 'completed'
    ).all()
    today_revenue = sum(payment.amount for payment in today_payments)
    
    # Calculate monthly revenue data for chart
    current_month = datetime.now().month
    current_year = datetime.now().year
    monthly_data = []
    
    for i in range(6):
        month = (current_month - i) if (current_month - i) > 0 else (current_month - i + 12)
        year = current_year if (current_month - i) > 0 else (current_year - 1)
        
        month_start = datetime(year, month, 1)
        if month == 12:
            month_end = datetime(year + 1, 1, 1)
        else:
            month_end = datetime(year, month + 1, 1)
        
        month_revenue = db.session.query(db.func.sum(Payment.amount)).filter(
            Payment.payment_date >= month_start,
            Payment.payment_date < month_end,
            Payment.status == 'completed'
        ).scalar() or 0
        
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'revenue': float(month_revenue)
        })
    
    # Reverse to get chronological order
    monthly_data.reverse()
    
    # Get payments with pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Number of payments per page
    payments_pagination = query.order_by(Payment.payment_date.desc()).paginate(page=page, per_page=per_page)
    
    # Create stats dictionary
    stats = {
        'total_payments': total_payments,
        'total_revenue': float(total_revenue),
        'total_pending': float(total_pending),
        'today_revenue': float(today_revenue),
        'payment_methods': payment_methods,
        'monthly_data': monthly_data
    }
    
    return render_template(
        'admin/payments.html',
        payments=payments_pagination.items,
        pagination=payments_pagination,
        stats=stats,
        filter_type=payment_type,
        filter_status=status,
        filter_start_date=start_date,
        filter_end_date=end_date,
        search=search,
        now=now,
        today=today,
        first_day_of_month=first_day_of_month,
        first_day_of_year=first_day_of_year,
        date_filters=date_filters
    )

@admin.route('/admin/payments/<int:payment_id>/refund', methods=['POST'])
@login_required
@admin_required
def refund_payment(payment_id):
    """
    Process a payment refund
    
    This route allows admin users to refund a completed payment.
    The payment status will be updated to 'refunded'.
    """
    payment = Payment.query.get_or_404(payment_id)
    
    # Verify payment is eligible for refund (must be completed and not already refunded)
    if payment.status != 'completed':
        flash('Only completed payments can be refunded.', 'warning')
        return redirect(url_for('admin.payment_list'))
    
    try:
        # Update payment status to refunded
        payment.status = 'refunded'
        
        # Add a transaction record for the refund
        refund_note = f"Refund for payment #{payment.id}"
        
        # Optional: Create a new payment record for the refund transaction
        refund_transaction = Payment(
            booking_id=payment.booking_id,
            user_id=payment.user_id,
            amount=-payment.amount,  # Negative amount to indicate a refund
            payment_method=payment.payment_method,
            payment_date=datetime.now(),
            status='completed',
            is_late_fee=payment.is_late_fee,
            transaction_id=f"REFUND-{payment.id}"
        )
        
        db.session.add(refund_transaction)
        
        # Create notification about the refund
        from models.notification import Notification
        booking_reference = payment.booking.get_reference() if payment.booking else None
        Notification.create_payment_notification(
            user_id=payment.user_id,
            booking_id=payment.booking_id,
            payment_status='refunded',
            amount=payment.amount,
            booking_reference=booking_reference
        )
        
        # If this was a booking payment, update booking status accordingly
        if payment.booking and not payment.is_late_fee:
            # Add a note about the refund in the session
            flash(f'Booking #{payment.booking.id} payment has been refunded.', 'info')
            
            # Optionally update the booking status if needed
            # payment.booking.status = 'refunded'
        
        db.session.commit()
        flash(f'Payment #{payment_id} has been successfully refunded.', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred during the refund process: {str(e)}', 'danger')
    
    return redirect(url_for('admin.payment_list'))

@admin.route('/admin/payments/<int:payment_id>/complete', methods=['POST'])
@login_required
@admin_required
def complete_payment(payment_id):
    """
    Mark a pending payment as completed
    
    This route allows admin users to mark a pending payment as completed.
    """
    payment = Payment.query.get_or_404(payment_id)
    
    # Verify payment is eligible to be marked as completed
    if payment.status != 'pending':
        flash('Only pending payments can be marked as completed.', 'warning')
        return redirect(url_for('admin.payment_list'))
    
    try:
        # Update payment status to completed
        payment.status = 'completed'
        
        # Create notification about completed payment
        from models.notification import Notification
        booking_reference = payment.booking.get_reference() if payment.booking else None
        Notification.create_payment_notification(
            user_id=payment.user_id,
            booking_id=payment.booking_id,
            payment_status='completed',
            amount=payment.amount,
            booking_reference=booking_reference
        )
        
        # If this was a booking payment, update booking status accordingly
        if payment.booking and not payment.is_late_fee:
            # Update booking status to pending_approval if it's still pending
            if payment.booking.status == 'pending':
                payment.booking.status = 'pending_approval'
                flash(f'Booking #{payment.booking.id} has been updated to pending approval.', 'info')
                
                # Also create booking status notification
                Notification.create_booking_notification(
                    user_id=payment.booking.user_id,
                    booking_id=payment.booking.id,
                    booking_status='pending_approval',
                    booking_reference=booking_reference
                )
        
        db.session.commit()
        flash(f'Payment #{payment_id} has been marked as completed.', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while updating the payment: {str(e)}', 'danger')
    
    return redirect(url_for('admin.payment_list'))

@admin.route('/admin/payments/<int:payment_id>')
@login_required
@admin_required
def payment_details(payment_id):
    """
    View detailed information about a specific payment
    """
    payment = Payment.query.get_or_404(payment_id)
    
    # Get related refund transactions if any
    refund_transactions = Payment.query.filter_by(
        transaction_id=f"REFUND-{payment.id}"
    ).all()
    
    return render_template(
        'admin/payment_details.html',
        payment=payment,
        refund_transactions=refund_transactions
    )

@admin.route('/api/admin/bookings')
@login_required
@admin_required
def booking_list_api():
    booking_id = request.args.get('booking_id', '')
    user_id = request.args.get('user_id', '')
    status = request.args.get('status', '')
    date_range = request.args.get('date_range', '')
    location = request.args.get('location', '')

    query = Booking.query

    if booking_id:
        query = query.filter(Booking.id == booking_id)

    if user_id:
        query = query.filter(Booking.user_id == user_id)

    if status:
        query = query.filter(Booking.status == status)

    # Date range filters
    if date_range:
        today = datetime.now().date()
        if date_range == 'today':
            # Today's bookings
            query = query.filter(func.date(Booking.booking_date) == today)
        elif date_range == 'week':
            # This week's bookings
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            query = query.filter(
                func.date(Booking.booking_date) >= start_of_week,
                func.date(Booking.booking_date) <= end_of_week
            )
        elif date_range == 'month':
            # This month's bookings
            start_of_month = today.replace(day=1)
            last_day = calendar.monthrange(today.year, today.month)[1]
            end_of_month = today.replace(day=last_day)
            query = query.filter(
                func.date(Booking.booking_date) >= start_of_month,
                func.date(Booking.booking_date) <= end_of_month
            )

    # Location filter using JSON operators
    if location:
        # Build a collection of conditions to handle various location storage formats
        location_conditions = [
            # Standard JSON path for pickup.name
            db.cast(db.func.json_extract(Booking.locations, '$.pickup.name'), db.String) == location,
            # Direct string search in the JSON
            Booking.locations.cast(db.String).like(f'%"{location}"%')
        ]
        
        # Create the combined filter
        query = query.filter(db.or_(*location_conditions))

    # Get all bookings after applying filters
    bookings = query.all()

    # Prepare data for JSON response
    bookings_data = []
    for booking in bookings:
        user = User.query.get(booking.user_id)
        car = Car.query.get(booking.car_id) if booking.car_id else None
        
        booking_dict = {
            'id': booking.id,
            'user': {
                'id': user.id,
                'email': user.email,
                'name': f"{user.first_name} {user.last_name}" if user.first_name and user.last_name else user.email
            },
            'car': {
                'id': car.id,
                'year': car.year,
                'make': car.make,
                'model': car.model,
                'full_name': f"{car.year} {car.make} {car.model}"
            } if car else None,
            'start_date': booking.start_date.strftime('%Y-%m-%d'),
            'end_date': booking.end_date.strftime('%Y-%m-%d'),
            'pickup_location': booking.pickup_location or 'Branch Not Recorded',
            'total_cost': float(booking.total_cost),
            'status': booking.status,
            'booking_date': booking.booking_date.strftime('%Y-%m-%d %H:%M:%S') if booking.booking_date else None,
            'booking_reference': booking.get_reference(),
            'duration_days': booking.duration_days
        }
        bookings_data.append(booking_dict)

    return jsonify({
        'bookings': bookings_data,
        'count': len(bookings_data)
    }) 

@admin.route('/admin/bookings/debug-locations')
@login_required
@admin_required
def debug_booking_locations():
    """Debug route to examine how locations are stored in the database"""
    bookings = Booking.query.order_by(Booking.id).all()
    
    booking_info = []
    for booking in bookings:
        location_debug = {
            'id': booking.id,
            'raw_locations': booking.locations,
            'pickup_location_property': booking.pickup_location,
            'return_location_property': booking.return_location,
            'debug_locations': booking.debug_locations(),
            'json_extract_test': db.session.query(
                db.func.json_extract(Booking.locations, '$.pickup.name')
            ).filter(Booking.id == booking.id).scalar()
        }
        booking_info.append(location_debug)
    
    return render_template(
        'admin/debug_locations.html', 
        bookings=booking_info,
        title="Debug Booking Locations"
    )

@admin.route('/api/admin/users')
@login_required
@admin_required
def user_list_api():
    """API endpoint for filtering user data"""
    # Get filter parameters
    search_query = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    sort = request.args.get('sort', 'id_desc')
    
    # Start with base query
    query = User.query
    
    # Apply search filter
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(
            db.or_(
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term),
                User.email.ilike(search_term),
                User.username.ilike(search_term),
                User.phone_number.ilike(search_term)
            )
        )
    
    # Apply role filter
    if role_filter == 'admin':
        query = query.filter(User.is_admin == True)
    elif role_filter == 'user':
        query = query.filter(User.is_admin == False)
    
    # Apply status filter
    if status_filter == 'active':
        query = query.filter(User.is_active == True)
    elif status_filter == 'inactive':
        query = query.filter(User.is_active == False)
    
    # Apply sorting
    if sort == 'name_asc':
        query = query.order_by(User.first_name.asc(), User.last_name.asc())
    elif sort == 'name_desc':
        query = query.order_by(User.first_name.desc(), User.last_name.desc())
    elif sort == 'email_asc':
        query = query.order_by(User.email.asc())
    elif sort == 'email_desc':
        query = query.order_by(User.email.desc())
    elif sort == 'date_asc':
        query = query.order_by(User.registration_date.asc())
    elif sort == 'date_desc':
        query = query.order_by(User.registration_date.desc())
    elif sort == 'id_asc':
        query = query.order_by(User.id.asc())
    else:  # Default to id_desc
        query = query.order_by(User.id.desc())
    
    # Execute query
    users = query.all()
    
    # Convert to JSON-serializable format
    users_data = []
    for user in users:
        user_dict = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'full_name': f"{user.first_name} {user.last_name}" if user.first_name and user.last_name else user.email,
            'phone_number': user.phone_number or 'N/A',
            'is_admin': user.is_admin,
            'is_active': user.is_active,
            'registration_date': user.registration_date.strftime('%m/%d/%Y') if user.registration_date else 'N/A'
        }
        users_data.append(user_dict)
    
    return jsonify({
        'users': users_data,
        'count': len(users_data)
    })

@admin.route('/api/admin/payments')
@login_required
@admin_required
def payment_list_api():
    """API endpoint for filtering payment data"""
    # Get filter parameters
    payment_type = request.args.get('type', '')
    status = request.args.get('status', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    search = request.args.get('search', '')
    
    # Start with base query
    query = Payment.query
    
    # Apply filters
    if payment_type == 'booking':
        query = query.filter(Payment.is_late_fee == False)
    elif payment_type == 'late_fee':
        query = query.filter(Payment.is_late_fee == True)
        
    if status:
        query = query.filter(Payment.status == status)
        
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Payment.payment_date >= start_date_obj)
        except ValueError:
            pass
            
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            # Add one day to include the end date fully
            end_date_obj = end_date_obj + timedelta(days=1)
            query = query.filter(Payment.payment_date < end_date_obj)
        except ValueError:
            pass
            
    if search:
        # Join with User and Booking to allow searching by user name or booking reference
        query = query.join(User, Payment.user_id == User.id)
        query = query.outerjoin(Booking, Payment.booking_id == Booking.id)
        
        # Apply search filters
        search_term = f"%{search}%"
        or_conditions = [
            Payment.payment_method.ilike(search_term),
            User.username.ilike(search_term),
            User.email.ilike(search_term),
            # Only include booking_reference if it exists in the Booking model
            Booking.booking_reference.ilike(search_term) if hasattr(Booking, 'booking_reference') else False,
            # Add other conditions as needed
        ]
        query = query.filter(
            db.or_(
                *or_conditions
            )
        )
    
    # Get payments ordered by date (newest first)
    payments = query.order_by(Payment.payment_date.desc()).all()
    
    # Convert to JSON-serializable format
    payments_data = []
    for payment in payments:
        # Get user info if available
        user_info = None
        if payment.user:
            user_info = {
                'id': payment.user.id,
                'name': f"{payment.user.first_name} {payment.user.last_name}",
                'email': payment.user.email
            }
        
        # Get booking info if available
        booking_info = None
        if payment.booking:
            booking_info = {
                'id': payment.booking.id,
                'reference': payment.booking.get_reference() if hasattr(payment.booking, 'get_reference') else f"BK-{payment.booking.id}"
            }
        
        # Format the payment data
        payment_dict = {
            'id': payment.id,
            'amount': float(payment.amount),
            'payment_method': payment.payment_method,
            'payment_date': payment.payment_date.strftime('%Y-%m-%d %H:%M') if payment.payment_date else None,
            'status': payment.status,
            'is_late_fee': payment.is_late_fee,
            'transaction_id': payment.transaction_id,
            'user': user_info,
            'booking': booking_info
        }
        
        payments_data.append(payment_dict)
    
    # Get payment statistics (similar to those in payment_list)
    total_payments = Payment.query.count()
    total_revenue = db.session.query(db.func.sum(Payment.amount)).filter(Payment.status == 'completed').scalar() or 0
    total_pending = db.session.query(db.func.sum(Payment.amount)).filter(Payment.status == 'pending').scalar() or 0
    
    return jsonify({
        'payments': payments_data,
        'count': len(payments_data),
        'stats': {
            'total_payments': total_payments,
            'total_revenue': float(total_revenue),
            'total_pending': float(total_pending)
        }
    })

@admin.route('/admin/content/about-us', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_about_us():
    """Admin route for editing the About Us page content"""
    # Get existing about us content or create a new one if it doesn't exist
    about_content = PageContent.query.filter_by(page_name='about_us').first()
    
    if not about_content:
        # Create default content if none exists
        about_content = PageContent(
            page_name='about_us',
            title='About JDM Car Rentals',
            content="""
            <p>Welcome to JDM Car Rentals, your premier destination for authentic Japanese Domestic Market vehicles.</p>
            
            <h2>Our Story</h2>
            <p>Founded in 2019, JDM Car Rentals has grown from a small collection of sports cars to a diverse fleet 
            of Japan's finest automobiles. Our passion for Japanese engineering excellence drives us to provide 
            an unparalleled driving experience for car enthusiasts and casual drivers alike.</p>
            
            <h2>Our Mission</h2>
            <p>At JDM Car Rentals, our mission is to share the joy of driving exceptional Japanese vehicles with 
            everyone. We believe that everyone deserves to experience the precision, reliability, and thrill that 
            JDM cars are known for worldwide.</p>
            
            <h2>Our Fleet</h2>
            <p>Our carefully curated selection includes iconic models from manufacturers like Toyota, Honda, Nissan, 
            Mazda, and Subaru. From the legendary Nissan Skyline GT-R to the nimble Honda S2000, our fleet represents 
            the pinnacle of Japanese automotive craftsmanship.</p>
            
            <h2>Customer Service</h2>
            <p>We pride ourselves on exceptional customer service. Our team of dedicated professionals is committed to 
            ensuring your rental experience is seamless from booking to return. We're always available to answer any 
            questions and provide assistance whenever needed.</p>
            """,
            last_updated_by=current_user.id
        )
        db.session.add(about_content)
        db.session.commit()
    
    if request.method == 'POST':
        # Update the content with the submitted data
        title = request.form.get('title')
        content = request.form.get('content')
        
        if not title or not content:
            flash('Title and content are required.', 'danger')
            return redirect(url_for('admin.edit_about_us'))
        
        about_content.title = title
        about_content.content = content
        about_content.last_updated_by = current_user.id
        about_content.last_updated = datetime.utcnow()
        
        db.session.commit()
        flash('About Us page content updated successfully!', 'success')
        return redirect(url_for('admin.edit_about_us'))
    
    return render_template('admin/content/edit_about_us.html', about_content=about_content)

@admin.route('/api/admin/reviews')
@login_required
@admin_required
def review_list_api():
    """API endpoint for review filtering"""
    # Get filter parameters
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    rating = request.args.get('rating', '')
    car_id = request.args.get('car_id', '')
    sort = request.args.get('sort', 'date_desc')
    
    # Base query
    query = Review.query
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        # Join with User and Car tables to search related fields
        query = query.join(User, Review.user_id == User.id)
        query = query.join(Car, Review.car_id == Car.id)
        
        query = query.filter(
            db.or_(
                Review.review_text.ilike(search_term),
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term),
                User.email.ilike(search_term),
                Car.make.ilike(search_term),
                Car.model.ilike(search_term)
            )
        )
    
    # Apply status filter
    if status == 'approved':
        query = query.filter(Review.is_approved == True)
    elif status == 'pending':
        query = query.filter(Review.is_approved == False)
    
    # Apply rating filter
    if rating and rating.isdigit():
        query = query.filter(Review.rating == int(rating))
    
    # Apply car filter
    if car_id and car_id.isdigit():
        query = query.filter(Review.car_id == int(car_id))
    
    # Apply sorting
    if sort == 'date_asc':
        query = query.order_by(Review.created_at.asc())
    elif sort == 'date_desc':
        query = query.order_by(Review.created_at.desc())
    elif sort == 'rating_asc':
        query = query.order_by(Review.rating.asc())
    elif sort == 'rating_desc':
        query = query.order_by(Review.rating.desc())
    else:
        # Default sort by newest
        query = query.order_by(Review.created_at.desc())
    
    # Fetch the reviews
    reviews = query.all()
    
    # Serialize the reviews
    review_list = []
    for review in reviews:
        review_data = {
            'id': review.id,
            'review_text': review.review_text,
            'rating': review.rating,
            'created_at': review.created_at.strftime('%Y-%m-%d %H:%M'),
            'is_approved': review.is_approved,
            'user': {
                'id': review.user.id,
                'name': f"{review.user.first_name} {review.user.last_name}",
                'email': review.user.email
            } if review.user else None,
            'car': {
                'id': review.car.id,
                'make': review.car.make,
                'model': review.car.model,
                'year': review.car.year
            } if review.car else None
        }
        review_list.append(review_data)
    
    # Get unique cars with reviews for car filter dropdown
    cars_with_reviews = db.session.query(Car.id, Car.make, Car.model, Car.year)\
        .join(Review, Car.id == Review.car_id)\
        .distinct()\
        .order_by(Car.make, Car.model)\
        .all()
    
    cars_list = [{'id': car.id, 'name': f"{car.make} {car.model} ({car.year})"} for car in cars_with_reviews]
    
    return jsonify({
        'reviews': review_list,
        'count': len(review_list),
        'filter_data': {
            'cars': cars_list
        }
    })

@admin.route('/admin/bookings/<int:booking_id>/reject-return', methods=['POST'])
@login_required
@admin_required
def reject_car_return(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Only pending_return bookings can be rejected
    if booking.status != 'pending_return':
        flash('Only pending returns can be rejected.', 'danger')
        return redirect(url_for('admin.booking_details', booking_id=booking_id))
    
    # Get form data
    damage_description = request.form.get('damage_description', '')
    damage_fee = float(request.form.get('damage_fee', 0))
    
    if damage_fee < 0:
        flash('Damage fee cannot be negative.', 'danger')
        return redirect(url_for('admin.booking_details', booking_id=booking_id))
    
    try:
        # Create a new payment record for the damage fee
        from models.payment import Payment
        damage_payment = Payment(
            booking_id=booking.id,
            user_id=booking.user_id,
            amount=damage_fee,
            payment_method='pending',
            status='pending',
            is_damage_fee=True,  # Mark this as a damage fee
            damage_description=damage_description,
            created_at=datetime.utcnow(),
            payment_date=None  # Will be set when paid
        )
        db.session.add(damage_payment)
        
        from models.notification import Notification
        user = User.query.get(booking.user_id)
        user_name = f"{user.first_name} {user.last_name}"
        
        Notification.create_damage_fee_notification(
            user_id=booking.user_id,
            booking_id=booking.id,
            amount=damage_fee,
            damage_description=damage_description,
            booking_reference=booking.get_reference()
        )
        
        Notification.create_admin_damage_notification(
            booking_id=booking.id,
            user_name=user_name,
            amount=damage_fee,
            damage_description=damage_description,
            booking_reference=booking.get_reference()
        )
        
        booking.status = 'confirmed'  
        booking.return_date = None  
        
        db.session.commit()
        flash(f'Return rejected. Customer has been charged ₱{damage_fee:.2f} for damages.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing return rejection: {str(e)}', 'danger')
    
    return redirect(url_for('admin.booking_details', booking_id=booking_id))


