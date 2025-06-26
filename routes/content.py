from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db
from models.content import PageContent

content_bp = Blueprint('content', __name__)

@content_bp.route('/about-us')
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