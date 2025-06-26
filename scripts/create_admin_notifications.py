"""
Create Admin Notifications Script

This script creates notifications for admin users for all existing bookings.
Use this to update the database with admin notifications for bookings that were created
before the admin notification functionality was implemented.
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db
from models.notification import Notification
from models.user import User
from models.booking import Booking
from models.car import Car

def create_admin_notifications():
    """Create admin notifications for all existing bookings"""
    with app.app_context():
        # Get all admin users
        admin_users = User.query.filter_by(is_admin=True).all()
        
        if not admin_users:
            print("No admin users found in the database.")
            return
        
        print(f"Found {len(admin_users)} admin users.")
        
        # Get all bookings
        bookings = Booking.query.all()
        
        if not bookings:
            print("No bookings found in the database.")
            return
        
        print(f"Found {len(bookings)} bookings. Creating admin notifications...")
        
        # Create notifications for each booking
        for booking in bookings:
            # Get user and car details
            user = User.query.get(booking.user_id)
            car = Car.query.get(booking.car_id)
            
            if not user or not car:
                print(f"Missing user or car data for booking {booking.id}. Skipping...")
                continue
            
            user_name = f"{user.first_name} {user.last_name}"
            car_name = car.make + " " + car.model
            
            # Create a notification for each admin about this booking
            for admin in admin_users:
                # Create booking notification
                booking_notification = Notification(
                    user_id=admin.id,
                    booking_id=booking.id,
                    title='Booking Information',
                    message=f'Booking #{booking.get_reference()} was made by {user_name} for the {car_name}. Current status: {booking.status}.',
                    notification_type='booking_status',
                    created_at=booking.booking_date  # Set creation date to match booking date
                )
                db.session.add(booking_notification)
                
                # If the booking has a payment, create a payment notification too
                if booking.payment:
                    payment_notification = Notification(
                        user_id=admin.id,
                        booking_id=booking.id,
                        title='Payment Information',
                        message=f'Payment of ₱{booking.total_cost:.2f} for booking #{booking.get_reference()} by {user_name}. Status: {booking.payment.status}.',
                        notification_type='payment',
                        created_at=booking.payment.payment_date or booking.booking_date
                    )
                    db.session.add(payment_notification)
        
        # Commit all changes
        try:
            db.session.commit()
            print("Successfully created admin notifications for all bookings!")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin notifications: {str(e)}")

if __name__ == "__main__":
    print("Creating admin notifications for existing bookings...")
    create_admin_notifications()
    print("Done!") 