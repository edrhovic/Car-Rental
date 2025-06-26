import sys
import os
import uuid
from flask import Flask
from models import db
from models.booking import Booking

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    db.init_app(app)
    return app

def add_booking_references():
    app = create_app()
    
    with app.app_context():
        # Check if booking_reference exists in the model
        if not hasattr(Booking, 'booking_reference'):
            print("The booking_reference field does not exist in the Booking model.")
            print("You need to add the field to the model and run the migration first.")
            return
            
        # Get all bookings
        bookings = Booking.query.all()
        print(f"Found {len(bookings)} bookings in the database.")
        
        # Add booking_reference to each booking if it doesn't have one
        updated_count = 0
        for booking in bookings:
            # Skip if the booking already has a reference
            if hasattr(booking, 'booking_reference') and booking.booking_reference:
                continue
                
            # Generate a unique reference code
            booking.booking_reference = f"BK-{str(uuid.uuid4())[:8].upper()}"
            updated_count += 1
            
        # Commit changes to the database
        if updated_count > 0:
            try:
                db.session.commit()
                print(f"Successfully added booking references to {updated_count} bookings.")
            except Exception as e:
                db.session.rollback()
                print(f"Error saving booking references: {str(e)}")
        else:
            print("No bookings needed updating.")

if __name__ == '__main__':
    add_booking_references() 