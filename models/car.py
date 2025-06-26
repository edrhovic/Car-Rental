from models import db
from datetime import datetime
from sqlalchemy import func

class Car(db.Model):
    __tablename__ = 'cars'
    
    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    color = db.Column(db.String(30), nullable=False)
    license_plate = db.Column(db.String(20), unique=True, nullable=False)
    vin = db.Column(db.String(17), unique=True, nullable=False)
    daily_rate = db.Column(db.Float, nullable=False)
    transmission = db.Column(db.String(20), nullable=False)
    fuel_type = db.Column(db.String(20), nullable=False)
    seats = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    is_available = db.Column(db.Boolean, default=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='car', lazy=True, cascade="all, delete-orphan")
    reviews = db.relationship('Review', backref='car', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"Car('{self.make}', '{self.model}', '{self.year}', '{self.license_plate}')"
    
    @property
    def average_rating(self):
        """Calculate the average rating for this car from all reviews."""
        from models.review import Review
        result = db.session.query(func.avg(Review.rating)).filter(Review.car_id == self.id).scalar()
        return result or 0  # Return 0 if there are no reviews 