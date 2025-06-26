from flask import Blueprint, render_template, redirect, url_for, flash, request, session, make_response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import random
import string
import sys
import os
from flask_mail import Message
from email_utils import send_otp_email

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import db
from models.user import User

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already authenticated, redirect to home
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            flash('Please check your login details and try again.', 'danger')
            return redirect(url_for('auth.login'))
        
        # If the user is an admin, suggest using the admin login page
        if user.is_admin:
            flash('Admin users should use the admin login page.', 'info')
            return redirect(url_for('admin.admin_login'))
        
        # Login user with remember me option
        login_user(user, remember=remember, duration=timedelta(days=14))
        
        # Set up session
        session.permanent = True
        session['login_timestamp'] = datetime.now().timestamp()
        session['last_activity'] = datetime.now().timestamp()
        session['user_id'] = user.id
        session['_fresh'] = True
        
        # Ensure session is saved
        session.modified = True
        
        # Get next page from args or default to home
        next_page = request.args.get('next')
        if next_page:
            try:
                # Validate that next_page is a relative URL
                if not next_page.startswith('/'):
                    next_page = None
            except:
                next_page = None
        
        # Create response with cache control headers
        response = make_response(redirect(next_page or url_for('home')))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response
    
    # Add cache control headers to login page
    response = make_response(render_template('auth/login.html'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone_number = request.form.get('phone_number')
        address = request.form.get('address')
        driver_license = request.form.get('driver_license')
        date_of_birth = request.form.get('date_of_birth')
        
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Check if user already exists
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Check if email already exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Process date of birth
        if date_of_birth:
            dob_date = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
        else:
            flash('Date of birth is required.', 'danger')
            return redirect(url_for('auth.register'))
            
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            address=address,
            driver_license=driver_license,
            date_of_birth=dob_date
        )
        
        # Add user to database
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth.route('/logout')
@login_required
def logout():
    # Get the user_id before logging out for flash message
    user_id = current_user.id if current_user.is_authenticated else None
    
    # Clear session data first
    session.clear()
    
    # Then logout the user
    logout_user()
    
    flash('You have been logged out.', 'info')
    
    # Create response with cache control headers
    response = make_response(redirect(url_for('home')))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    
    # Clear any cookies by setting them to expire
    if user_id:
        response.set_cookie('remember_token', '', expires=0)
        response.set_cookie('session', '', expires=0)
    
    return response

@auth.route('/terms')
def terms():
    return render_template('auth/terms.html')

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('No account found with that email address.', 'danger')
            return redirect(url_for('auth.forgot_password'))
        
        # Generate 6-digit OTP
        otp = ''.join(random.choices(string.digits, k=6))
        
        # Store OTP in session with expiration time (5 minutes)
        expiry_time = datetime.utcnow() + timedelta(minutes=5)
        session['reset_email'] = email
        session['reset_otp'] = otp
        session['reset_otp_expiry'] = expiry_time.timestamp()
        
        # Send OTP email with better error handling
        success, message = send_otp_email(email, otp)
        if success:
            flash('OTP sent to your email address. Please check your inbox and spam folder.', 'success')
            return redirect(url_for('auth.verify_otp', email=email))
        else:
            if "authorized" in message.lower():
                flash('Your email needs to be authorized in our system first. Please check your inbox for an authorization email from Mailgun or contact support.', 'warning')
            elif "timeout" in message.lower():
                flash('The email service is temporarily unavailable. Please try again in a few minutes.', 'warning')
            elif "connection" in message.lower():
                flash('Unable to connect to the email service. Please try again in a few minutes.', 'warning')
            else:
                flash(f'Error sending OTP: {message}', 'danger')
            return redirect(url_for('auth.forgot_password'))
    
    return render_template('auth/forgot_password.html')

@auth.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    email = request.args.get('email') or request.form.get('email')
    
    # Check if we have a reset in progress
    if not email or 'reset_email' not in session or session['reset_email'] != email:
        flash('Password reset session expired or invalid. Please try again.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    # Check if OTP has expired
    if 'reset_otp_expiry' in session:
        expiry_time = datetime.fromtimestamp(session['reset_otp_expiry'])
        if datetime.utcnow() > expiry_time:
            # Clear session data
            session.pop('reset_email', None)
            session.pop('reset_otp', None)
            session.pop('reset_otp_expiry', None)
            
            flash('OTP has expired. Please request a new one.', 'danger')
            return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        submitted_otp = request.form.get('otp')
        stored_otp = session.get('reset_otp')
        
        # Debug logs (remove in production)
        print(f"Submitted OTP: {submitted_otp}")
        print(f"Stored OTP: {stored_otp}")
        
        if not submitted_otp or submitted_otp != stored_otp:
            flash('Invalid OTP. Please try again.', 'danger')
            return redirect(url_for('auth.verify_otp', email=email))
        
        # Generate a secure token for password reset
        reset_token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        session['reset_token'] = reset_token
        
        # Redirect to the reset password page
        return redirect(url_for('auth.reset_password', email=email, token=reset_token))
    
    return render_template('auth/verify_otp.html', email=email)

@auth.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    email = request.args.get('email') or request.form.get('email')
    token = request.args.get('token') or request.form.get('token')
    
    # Validate token and email
    if not email or not token or 'reset_email' not in session or session['reset_email'] != email or 'reset_token' not in session or session['reset_token'] != token:
        flash('Invalid or expired password reset link. Please try again.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.reset_password', email=email, token=token))
        
        # Update user's password
        user = User.query.filter_by(email=email).first()
        if user:
            user.password_hash = generate_password_hash(password)
            db.session.commit()
            
            # Clear session data
            session.pop('reset_email', None)
            session.pop('reset_otp', None)
            session.pop('reset_otp_expiry', None)
            session.pop('reset_token', None)
            
            flash('Your password has been updated successfully! You can now log in with your new password.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('User not found.', 'danger')
            return redirect(url_for('auth.forgot_password'))
    
    return render_template('auth/reset_password.html', email=email, token=token) 