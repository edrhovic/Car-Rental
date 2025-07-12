from datetime import datetime
from models import db

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(50), nullable=False)  # credit_card, debit_card, paypal, etc.
    transaction_id = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, completed, failed, refunded
    is_late_fee = db.Column(db.Boolean, default=False)  # Flag to identify late fee payments
    late_fee_amount = db.Column(db.Float, default=0.0)  # Amount of late fee if applicable
    is_damage_fee = db.Column(db.Boolean, default=False)  # Flag to identify damage fee payments
    damage_description = db.Column(db.Text, nullable=True)  # Description of damage if applicable
    
    # Card payment information fields
    card_holder_name = db.Column(db.String(100), nullable=True)  # Name on the card
    card_number = db.Column(db.String(20), nullable=True)  # Full card number (for admin viewing)
    card_last_four = db.Column(db.String(4), nullable=True)  # Last 4 digits for display
    card_expiry = db.Column(db.String(5), nullable=True)  # Expiry date in MM/YY format
    card_type = db.Column(db.String(20), nullable=True)  # Visa, MasterCard, etc.
    
    # Define the relationship to Booking
    booking = db.relationship('Booking', back_populates='payment', foreign_keys=[booking_id], lazy=True)
    user = db.relationship('User', backref='payments', foreign_keys=[user_id], lazy=True)
    
    def __repr__(self):
        return f'<Payment {self.id} - ${self.amount:.2f} - {self.status}>' 