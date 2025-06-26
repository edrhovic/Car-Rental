from flask import Flask, render_template, redirect, url_for, flash, request, session, make_response
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from flask_mail import Mail
from flask_session import Session
import os
from datetime import datetime, timedelta
from models import db
import requests
import sys
from functools import wraps
from markupsafe import Markup
import urllib3
import json
from urllib3.util.retry import Retry

# Initialize Flask app
app = Flask(__name__)

# Initialize extensions
mail = Mail()
sess = Session()

# Configure app
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 
                                                     'mysql+pymysql://root:041405EdRhovic@localhost:3306/jdm_car_rentals')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)  # Session timeout after 2 hours
app.config['SESSION_REFRESH_EACH_REQUEST'] = True  # Update session on each request
app.config['SESSION_TYPE'] = 'filesystem'  # Store sessions in filesystem
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')  # Session file directory
app.config['SESSION_FILE_THRESHOLD'] = 500  # Maximum number of sessions stored on disk
app.config['SESSION_COOKIE_SECURE'] = False  # Allow cookies over HTTP for development
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['REMEMBER_COOKIE_SECURE'] = False  # Allow remember me over HTTP for development
app.config['REMEMBER_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to remember cookie
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=14)  # Remember me duration
app.config['REMEMBER_COOKIE_REFRESH_EACH_REQUEST'] = True  # Update remember cookie on each request
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Prevent caching of static files
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Auto reload templates

# Create session directory if it doesn't exist
if not os.path.exists(app.config['SESSION_FILE_DIR']):
    os.makedirs(app.config['SESSION_FILE_DIR'])

# Initialize Flask-Session
sess.init_app(app)

# Import email utilities
from email_utils import send_email

# Mailgun configuration - updated with valid keys
MAILGUN_API_KEY = '14d3e67081b204e02167d8401cb15d28-f6202374-6f9ddbb8'
MAILGUN_DOMAIN = 'sandbox0f57da4bf0b84771bdfe824bb9ea93d4.mailgun.org'
MAILGUN_SENDER = 'JDM Car Rentals <mailgun@sandbox0f57da4bf0b84771bdfe824bb9ea93d4.mailgun.org>'

# Set environment variables for email_utils
os.environ['MAILGUN_API_KEY'] = MAILGUN_API_KEY
os.environ['MAILGUN_DOMAIN'] = MAILGUN_DOMAIN
os.environ['MAILGUN_SENDER'] = MAILGUN_SENDER

# Print email configuration for debugging
print("Mailgun Email Configuration:")
print(f"Mailgun API Key: {MAILGUN_API_KEY[:5]}...{MAILGUN_API_KEY[-5:]}")
print(f"Mailgun Domain: {MAILGUN_DOMAIN}")
print(f"Mailgun Sender: {MAILGUN_SENDER}")

# Initialize database with the app
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

# Initialize urllib3 with retries and longer timeouts
http = urllib3.PoolManager(
    retries=Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504]
    ),
    timeout=urllib3.Timeout(connect=10.0, read=30.0)
)

# Email service function using Mailgun
def send_email(to_email, subject, html_content):
    """Send email using Mailgun's API"""
    try:
        print(f"Sending email via Mailgun to {to_email}")
        print(f"Subject: {subject}")
        
        url = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"
        
        # Encode credentials
        import base64
        credentials = base64.b64encode(f"api:{MAILGUN_API_KEY}".encode()).decode()
        
        headers = {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Prepare form data
        fields = {
            'from': MAILGUN_SENDER,
            'to': to_email,
            'subject': subject,
            'html': html_content
        }
        
        # Send email via Mailgun API with improved error handling
        try:
            response = http.request(
                'POST',
                url,
                fields=fields,
                headers=headers,
                timeout=urllib3.Timeout(connect=10.0, read=30.0),
                retries=3
            )
            
            # Log response for debugging
            print(f"Mailgun API Response Status: {response.status}")
            try:
                response_data = json.loads(response.data.decode())
                print(f"Response body: {response_data}")
            except json.JSONDecodeError:
                print(f"Raw response: {response.data.decode()}")
            
            if response.status == 200:
                print("Email sent successfully!")
                return True, "Email sent successfully"
            elif response.status == 401:
                error_msg = "Authentication failed. Please check your API key."
                print(error_msg)
                return False, error_msg
            elif response.status == 402:
                error_msg = "Request failed. Please check if your account has sufficient credits."
                print(error_msg)
                return False, error_msg
            elif response.status == 404:
                error_msg = "Domain not found. Please check your domain configuration."
                print(error_msg)
                return False, error_msg
            elif response.status == 422:
                error_msg = "The recipient email needs to be authorized in the Mailgun sandbox domain first. Please check your inbox for the authorization email or contact support."
                print(error_msg)
                return False, error_msg
            else:
                error_msg = f"Unexpected status code: {response.status}"
                print(error_msg)
                return False, error_msg
                
        except urllib3.exceptions.MaxRetryError as e:
            error_msg = f"Connection failed after multiple retries: {str(e)}"
            print(error_msg)
            return False, error_msg
        except urllib3.exceptions.TimeoutError as e:
            error_msg = f"Request timed out: {str(e)}"
            print(error_msg)
            return False, error_msg
        except urllib3.exceptions.ConnectTimeoutError as e:
            error_msg = f"Connection timed out: {str(e)}"
            print(error_msg)
            return False, error_msg
        except urllib3.exceptions.ConnectionError as e:
            error_msg = f"Connection error: {str(e)}"
            print(error_msg)
            return False, error_msg
            
    except Exception as e:
        error_msg = f"Error sending email: {str(e)}"
        print(error_msg)
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False, error_msg

# For backwards compatibility
send_email_with_mailgun = send_email

# Import models
from models.user import User
from models.car import Car
from models.booking import Booking
from models.review import Review
from models.payment import Payment
from models.content import PageContent
from models.notification import Notification

# Import blueprints
from routes.auth import auth
from routes.user import user
from routes.admin import admin
from routes.car import car
from routes.booking import booking
from routes.notification import notification_bp
from routes.contact import contact_bp

# Register blueprints
# We don't need the main blueprint since it appears not to exist
app.register_blueprint(auth)
app.register_blueprint(user)
app.register_blueprint(admin)
app.register_blueprint(car)
app.register_blueprint(booking)
app.register_blueprint(notification_bp, url_prefix='/notification', name='notification')
app.register_blueprint(contact_bp)

# Session security settings
@app.before_request
def before_request():
    # Skip session validation for static files and health checks
    if request.path.startswith('/static'):
        return
        
    # Check if user is authenticated
    if current_user.is_authenticated:
        # Make session permanent
        session.permanent = True
        
        # Get last activity time
        last_active = session.get('last_activity')
        
        if last_active is not None:
            # Calculate inactivity time
            inactive_time = datetime.now() - datetime.fromtimestamp(last_active)
            
            # Check if session has timed out (30 minutes)
            if inactive_time > timedelta(minutes=30):
                # Log the timeout
                app.logger.warning(f"Session timeout for user {current_user.id}")
                
                # Clear session
                session.clear()
                
                # Logout user
                logout_user()
                
                # Flash message and redirect
                flash('Your session has expired. Please login again.', 'warning')
                return redirect(url_for('auth.login'))
        
        # Update last activity time
        session['last_activity'] = datetime.now().timestamp()
        
        # Mark session as modified
        session.modified = True

# Add cache control headers to prevent back-button issues
@app.after_request
def add_header(response):
    # Prevent caching for authenticated pages
    if current_user.is_authenticated:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

# Custom decorator to require fresh login for sensitive actions
def fresh_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            # Check how long ago the user logged in
            login_timestamp = session.get('login_timestamp')
            if not login_timestamp or (datetime.now().timestamp() - login_timestamp) > 3600:  # 1 hour
                flash('For your security, please login again to perform this action.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(id):
    return db.session.get(User, int(id))

@app.route('/')
def home():
    cars = Car.query.filter_by(is_available=True).all()
    # Fetch a few recent reviews to display on the homepage
    from models.review import Review
    from models.user import User
    recent_reviews = db.session.query(Review).join(User).filter(Review.is_approved == True).order_by(Review.review_date.desc()).limit(3).all()
    
    return render_template('index.html', cars=cars, recent_reviews=recent_reviews)

@app.route('/about-us')
def about_us():
    """Display the About Us page"""
    # Get the about us content from the database or use a default if not found
    about_content = PageContent.query.filter_by(page_name='about_us').first()
    
    # If no content exists in the database, use default content
    if not about_content:
        about_content = {
            'title': 'About JDM Car Rentals',
            'content': """
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
            """
        }
    
    return render_template('content/about_us.html', about_content=about_content)

@app.route('/contact')
def contact():
    """Redirect to the contact page in the contact blueprint"""
    return redirect(url_for('contact.contact_page'))

@app.route('/contact-submit', methods=['POST'])
def contact_submit():
    """Redirect to the contact_submit route in the contact blueprint"""
    return redirect(url_for('contact.contact_submit'))

# Redirect route for old notifications URL
@app.route('/notifications')
def redirect_notifications():
    """Redirect from old /notifications URL to new /notification URL"""
    return redirect(url_for('notification.list_notifications'))

# Redirect routes for other notification endpoints
@app.route('/notifications/unread')
def redirect_unread():
    return redirect(url_for('notification.unread_count'))

@app.route('/notifications/mark-read/<int:notification_id>', methods=['POST'])
def redirect_mark_read(notification_id):
    return redirect(url_for('notification.mark_as_read', notification_id=notification_id))

@app.route('/notifications/mark-all-read', methods=['POST'])
def redirect_mark_all_read():
    return redirect(url_for('notification.mark_all_read'))

@app.route('/notifications/delete/<int:notification_id>', methods=['POST'])
def redirect_delete_notification(notification_id):
    return redirect(url_for('notification.delete_notification', notification_id=notification_id))

@app.route('/api/notifications/latest')
def redirect_latest_notifications():
    return redirect(url_for('notification.get_latest_notifications'))

# Add context processors to make certain variables available to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Test route for email functionality
@app.route('/test-email')
def test_email():
    if not current_user.is_authenticated or not current_user.is_admin:
        return "Unauthorized", 403
    
    try:
        recipient = request.args.get('email', current_user.email)
        result = send_email(
            recipient,
            "JDM Car Rentals - Test Email",
            "<h1>Test Email</h1><p>This is a test email from JDM Car Rentals.</p>"
        )
        
        if result:
            return f"Email sent successfully to {recipient}!"
        else:
            return f"Failed to send email to {recipient}. Check server logs for details."
    except Exception as e:
        return f"Error: {str(e)}"

# Debug route for email configuration
@app.route('/debug-email-config')
def debug_email_config():
    if not current_user.is_authenticated or not current_user.is_admin:
        return "Unauthorized", 403
        
    config_info = {
        'MAILGUN_API_KEY': f"{MAILGUN_API_KEY[:5]}...{MAILGUN_API_KEY[-5:]}",
        'MAILGUN_DOMAIN': MAILGUN_DOMAIN,
        'MAILGUN_SENDER': MAILGUN_SENDER,
        'Email Module': 'requests' in sys.modules,
        'Python Version': sys.version
    }
    
    return render_template('admin/debug/email_config.html', config=config_info)

# Add custom template filters
@app.template_filter('nl2br')
def nl2br_filter(s):
    if not s:
        return ""
    return Markup(s.replace('\n', '<br>\n'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0') 

