from models import db
from datetime import datetime

class LoanCar(db.Model):
    __tablename__ = 'loan_cars'
    
    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey('cars.id'), nullable=False)
    loan_sale_price = db.Column(db.Float, nullable=False)
    commission_rate = db.Column(db.Float, default=30.0)
    
    # Status management
    status = db.Column(db.String(20), default='available')  # available, pending, approved, active, sold
    date_offered = db.Column(db.DateTime, default=datetime.utcnow)
    activated_at = db.Column(db.DateTime, nullable=True)
    is_available = db.Column(db.Boolean, default=True)
    
    # Legacy fields (keep for backwards compatibility)
    is_sold_via_loan = db.Column(db.Boolean, default=False)
    date_sold = db.Column(db.DateTime, nullable=True)
    loan_system_id = db.Column(db.String(50), nullable=True)
    offered_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    car = db.relationship('Car', backref='loan_offer', lazy=True)
    admin = db.relationship('User', backref='loan_cars_offered', lazy=True)
    loan_sales = db.relationship('LoanSale', backref='loan_car', lazy=True)
    
    def __repr__(self):
        return f"<LoanCar CarID={self.car_id}, Price={self.loan_sale_price}, Status={self.status}>"

class LoanSale(db.Model):
    __tablename__ = 'loan_sales'
    
    id = db.Column(db.Integer, primary_key=True)
    loan_car_id = db.Column(db.Integer, db.ForeignKey('loan_cars.id'), nullable=False)
    
    # Borrower information
    borrower_name = db.Column(db.String(100), nullable=False)
    borrower_email = db.Column(db.String(120), nullable=False)
    borrower_phone = db.Column(db.String(20), nullable=True)
    
    # Loan details
    loan_term_months = db.Column(db.Integer, nullable=False)
    interest_rate = db.Column(db.Float, nullable=True)
    monthly_payment = db.Column(db.Float, nullable=False)
    
    # Sale and system tracking
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)
    loan_system_reference = db.Column(db.String(100), nullable=True)
    
    # Commission tracking
    total_commission_expected = db.Column(db.Float, nullable=False)
    commission_received = db.Column(db.Float, default=0.0)
    date_commission_received = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f"<LoanSale {self.id} - {self.borrower_name}>"