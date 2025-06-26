from datetime import datetime, date
from models import db
import uuid
import json

class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey('cars.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    booking_reference = db.Column(db.String(20), unique=True, default=lambda: f"BK-{str(uuid.uuid4())[:8].upper()}")
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    locations = db.Column(db.JSON, nullable=True)
    total_cost = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, confirmed, pending_return, completed, cancelled
    returned = db.Column(db.Boolean, default=False)
    return_date = db.Column(db.DateTime, nullable=True)
    is_late_return = db.Column(db.Boolean, default=False)  # Flag for late returns
    late_fee = db.Column(db.Float, default=0.0)  # The total late fee charged
    late_fee_paid = db.Column(db.Boolean, default=False)  # Flag to check if late fee is paid
    
    # Relationships
    payment = db.relationship('Payment', back_populates='booking', uselist=False, lazy=True)
    review = db.relationship('Review', backref='booking', uselist=False, lazy=True)
    
    def __repr__(self):
        return f'<Booking {self.id} - {self.status}>'
        
    def get_reference(self):
        """Get a booking reference, even if the field doesn't exist in the database yet"""
        try:
            if hasattr(self, 'booking_reference') and self.booking_reference:
                return self.booking_reference
        except:
            pass
        return f"BK-{self.id}"
    
    @property
    def pickup_location(self):
        """Get pickup location from the JSON locations field"""
        if self.locations:
            try:
                locations_data = self.locations
                if isinstance(locations_data, str):
                    locations_data = json.loads(locations_data)
                
                # Handle different potential JSON structures
                if isinstance(locations_data, dict):
                    # New format with pickup/return keys
                    if 'pickup' in locations_data and isinstance(locations_data['pickup'], dict):
                        return locations_data['pickup'].get('name', 'Branch Not Recorded')
                    
                    # Legacy format with just a name
                    elif 'name' in locations_data:
                        return locations_data['name']
                
                # If it's a string, try to use it directly
                elif isinstance(locations_data, str) and locations_data.strip():
                    return locations_data
            except Exception as e:
                print(f"Error parsing location data for booking: {str(e)}")
        
        return 'Branch Not Recorded'
    
    @property
    def return_location(self):
        """Get return location from the JSON locations field"""
        if self.locations:
            try:
                locations_data = self.locations
                if isinstance(locations_data, str):
                    locations_data = json.loads(locations_data)
                
                # Handle different potential JSON structures
                if isinstance(locations_data, dict):
                    # New format with pickup/return keys
                    if 'return' in locations_data and isinstance(locations_data['return'], dict):
                        return locations_data['return'].get('name', 'Branch Not Recorded')
                    
                    # If no specific return location, use pickup location (common case)
                    elif 'pickup' in locations_data and isinstance(locations_data['pickup'], dict):
                        return locations_data['pickup'].get('name', 'Branch Not Recorded')
                    
                    # Legacy format with just a name
                    elif 'name' in locations_data:
                        return locations_data['name']
                
                # If it's a string, try to use it directly
                elif isinstance(locations_data, str) and locations_data.strip():
                    return locations_data
            except Exception as e:
                print(f"Error parsing location data for booking: {str(e)}")
        
        return 'Branch Not Recorded'
        
    @property
    def is_active(self):
        return self.status in ['confirmed', 'pending'] and not self.returned
        
    @property
    def duration_days(self):
        delta = self.end_date - self.start_date
        return delta.days + 1  # Include both start and end days
    
    @property
    def is_overdue(self):
        """Check if the booking is past the end date but not returned yet"""
        today = date.today()
        return today > self.end_date and not self.returned and self.status == 'confirmed'
    
    def calculate_late_fee(self):
        """Calculate late fee as 150% of daily rate for each day past the end date"""
        if not self.is_overdue:
            return 0.0
            
        today = date.today()
        days_late = (today - self.end_date).days
        from models.car import Car
        car = db.session.get(Car, self.car_id)
        if car:
            # Late fee is 150% of daily rate per day
            daily_late_fee = car.daily_rate * 1.5
            return daily_late_fee * days_late
        return 0.0
    
    def debug_locations(self):
        """Debug method to examine raw locations data"""
        try:
            if self.locations:
                if isinstance(self.locations, str):
                    return f"String: {self.locations}"
                elif isinstance(self.locations, dict):
                    return f"Dict: {self.locations}"
                else:
                    return f"Type: {type(self.locations)}, Value: {self.locations}"
            else:
                return "No locations data"
        except Exception as e:
            return f"Error parsing locations: {str(e)}"

    @property
    def location(self):
        """Get the pickup location name (for backward compatibility)"""
        if not self.locations:
            return 'Branch Not Recorded'
        locations_data = json.loads(self.locations) if isinstance(self.locations, str) else self.locations
        return locations_data['pickup'].get('name', 'Branch Not Recorded')
        
    @property
    def car_details(self):
        """Get car details"""
        from models.car import Car
        car = db.session.get(Car, self.car_id)
        if car:
            return {
                'make': car.make,
                'model': car.model,
                'year': car.year,
                'color': car.color,
                'license_plate': car.license_plate,
                'daily_rate': car.daily_rate
            }
        return None 