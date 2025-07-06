from models import db
from datetime import datetime

class LoanCar(db.Model):
    __tablename__ = 'loan_cars'
    
    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey('cars.id'), nullable=False)
    loan_sale_price = db.Column(db.Float, nullable=False)
    commission_rate = db.Column(db.Float, default=5.0)
    
    # Status management
    status = db.Column(db.String(20), default='available')  # available, pending, approved, active
    date_offered = db.Column(db.DateTime, default=datetime.utcnow)
    activated_at = db.Column(db.DateTime, nullable=True)
    
    # Borrower information (populated when loan is activated)
    borrower_id = db.Column(db.Integer, nullable=True)
    borrower_name = db.Column(db.String(100), nullable=True)
    borrower_email = db.Column(db.String(120), nullable=True)
    borrower_phone = db.Column(db.String(20), nullable=True)
    
    # Loan details (populated when loan is activated)
    loan_amount = db.Column(db.Float, nullable=True)
    loan_term = db.Column(db.Integer, nullable=True)  # in months
    interest_rate = db.Column(db.Float, nullable=True)
    
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
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    loan_amount = db.Column(db.Float, nullable=False)
    loan_term_months = db.Column(db.Integer, nullable=False)
    monthly_payment = db.Column(db.Float, nullable=False)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)
    loan_system_reference = db.Column(db.String(100), nullable=True)
    
    total_commission_expected = db.Column(db.Float, nullable=False)
    commission_received = db.Column(db.Float, default=0.0)
    last_commission_payment = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f"<LoanSale {self.id} - {self.customer_name}>"

class LoanCommission(db.Model):
    __tablename__ = 'loan_commissions'
    
    id = db.Column(db.Integer, primary_key=True)
    loan_sale_id = db.Column(db.Integer, db.ForeignKey('loan_sales.id'), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)
    payment_month = db.Column(db.String(7), nullable=False)  # YYYY-MM format
    loan_system_reference = db.Column(db.String(100), nullable=True)
    
    # Relationship
    loan_sale = db.relationship('LoanSale', backref='commission_payments', lazy=True)
    
    def __repr__(self):
        return f"<LoanCommission {self.id} - ${self.amount}>"