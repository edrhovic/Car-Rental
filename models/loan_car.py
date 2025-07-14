# FIXED MODELS - Corrected foreign key references and model structure

from models import db
from datetime import datetime

class LoanCar(db.Model):
    __tablename__ = 'loan_cars'
    
    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey('cars.id'), nullable=False)
    loan_sale_price = db.Column(db.Float, nullable=False)
    commission_rate = db.Column(db.Float, default=10.0)
    
    # Status management
    status = db.Column(db.String(20), default='available')  # available, pending, approved, active, sold
    date_offered = db.Column(db.DateTime, default=datetime.utcnow)
    is_available = db.Column(db.Boolean, default=True)
    activated_at = db.Column(db.DateTime, nullable=True)
    # Relationships
    car = db.relationship('Car', backref='loan_car', lazy=True)
    loan_sales = db.relationship('LoanSale', backref='loan_car', lazy=True)
    
    def __repr__(self):
        return f"<LoanCar CarID={self.car_id}, Price={self.loan_sale_price}, Status={self.status}>"

class LoanSale(db.Model):
    __tablename__ = 'loan_sales'
    
    id = db.Column(db.Integer, primary_key=True)
    loan_car_id = db.Column(db.Integer, db.ForeignKey('loan_cars.id'), nullable=True)
    disbursement_id = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer, nullable=True)
    first_name = db.Column(db.String(120), nullable=False)
    middle_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    contact = db.Column(db.String(20), nullable=True)
    loan_term = db.Column(db.Integer, nullable=True)
    
    def __repr__(self):
        return f"<LoanSale {self.id} - {self.first_name} {self.last_name}>"
    
class LoanPayment(db.Model):
    __tablename__ = 'loan_payments'  # Fixed table name to be plural
    
    id = db.Column(db.Integer, primary_key=True)
    loan_sale_id = db.Column(db.Integer, db.ForeignKey('loan_sales.id'), nullable=False)    
    commission_received = db.Column(db.Float, default=0.0)
    date_commission_received = db.Column(db.DateTime, nullable=True)
    monthly_payment = db.Column(db.Float, nullable=True)
    total_commission_received = db.Column(db.Float, default=0.0)
    
    # Add relationship
    loan_sale = db.relationship('LoanSale', backref='loan_payments', lazy=True)
    
    def __repr__(self):
        return f"<LoanPayment {self.id} - ${self.commission_received} on {self.date_commission_received}>"
    
class LoanNotification(db.Model):
    __tablename__ = 'loan_notifications'

    id = db.Column(db.Integer, primary_key=True)
    loan_car_id = db.Column(db.Integer, db.ForeignKey('loan_cars.id'), nullable=True)
    loan_sale_id = db.Column(db.Integer, db.ForeignKey('loan_sales.id'), nullable=True)
    loan_payment_id = db.Column(db.Integer, db.ForeignKey('loan_payments.id'), nullable=True)
    
    
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    loan_car = db.relationship('LoanCar', backref='notifications', lazy=True)
    loan_sale = db.relationship('LoanSale', backref='notifications', lazy=True)
    payment = db.relationship('LoanPayment', backref='notifications', lazy=True)
    
    def __repr__(self):
        return f'<LoanNotification {self.id}: {self.title}>'
    
    @staticmethod
    def create_loan_status_notification(loan_car, status):
        """Create notification when loan car status changes"""
        
        # Get car details from relationship
        car = loan_car.car
        
        if status == 'pending':
            title = "Loan Application Under Review"
            message = f"The loan application for {car.make} {car.model} ({car.year}) is currently under review. We will notify you once the decision is made."
            notification_type = 'loan_pending'
            
        elif status == 'approved':
            title = "Loan Application Approved!"
            message = f"Congratulations! The loan application for {car.make} {car.model} ({car.year}) has been approved. Loan amount: ${loan_car.loan_sale_price:,.2f}."
            notification_type = 'loan_approved'
            
        elif status == 'rejected':
            title = "Loan Application Decision"
            message = f"Unfortunately, the loan application for {car.make} {car.model} ({car.year}) was not approved at this time. Please contact us for more information."
            notification_type = 'loan_rejected'
            
        else:
            return None
        
        notification = LoanNotification(
            loan_car_id=loan_car.id,
            title=title,
            message=message,
            notification_type=notification_type
        )
        
        db.session.add(notification)
        db.session.commit()
        return notification
    
    @staticmethod
    def create_payment_notification(payment):
        """Create notification when payment is received"""
        try:
            loan_sale = payment.loan_sale
            if not loan_sale:
                print("Error: LoanSale not found for payment")
                return None
                
            loan_car = loan_sale.loan_car
            if not loan_car:
                print("Error: LoanCar not found for loan_sale")
                return None
                
            car = loan_car.car
            if not car:
                print("Error: Car not found for loan_car")
                return None
            
            payment_months = (payment.commission_received / loan_car.loan_sale_price) * loan_sale.loan_term
            
            # Handle date formatting safely
            payment_date_str = "N/A"
            if payment.date_commission_received:
                try:
                    payment_date_str = payment.date_commission_received.strftime('%B %d, %Y')
                except Exception as e:
                    print(f"Error formatting date: {e}")
                    payment_date_str = str(payment.date_commission_received)
            
            # Handle disbursement_id safely
            disbursement_info = ""
            if loan_sale.disbursement_id:
                disbursement_info = f" Disbursement ID: {loan_sale.disbursement_id}"
            
            title = "Payment Received"
            message = f"Thank you! We have received your payment worth of {int(payment_months)} months. Amount paid: ${payment.monthly_payment * payment_months:,.2f} for {car.make} {car.model} ({car.year}). Payment date: {payment_date_str}.{disbursement_info}"
            
            notification = LoanNotification(
                loan_payment_id=payment.id,
                loan_car_id=loan_car.id,
                loan_sale_id=loan_sale.id,
                title=title,
                message=message,
                notification_type='payment_received'
            )
            return notification
        
        except Exception as e:
            print(f"Error creating payment notification: {e}")
            return None

    @staticmethod
    def last_payment_notification(payment):
        """Notify admin that the last payment for a particular car was received"""
        try:
            loan_sale = payment.loan_sale
            if not loan_sale:
                print("Error: LoanSale not found for payment")
                return None

            loan_car = loan_sale.loan_car
            if not loan_car:
                print("Error: LoanCar not found for loan_sale")
                return None

            car = loan_car.car
            if not car:
                print("Error: Car not found for loan_car")
                return None
            
            payment_date_str = "N/A"
            if payment.date_commission_received and loan_car.status == 'paid':
                try:
                    payment_date_str = payment.date_commission_received.strftime('%B %d, %Y')
                except Exception as e:
                    print(f"Error formatting date: {e}")
                    payment_date_str = str(payment.date_commission_received)

            title = "Last Payment Received"
            message = (
                f"The last payment for {car.make} {car.model} ({car.year}) has been received. "
                f"Amount: ${payment.commission_received:,.2f}. Payment date: {payment_date_str}."
                f"This car now is completely paid."
            )

            notification = LoanNotification(
                loan_payment_id=payment.id,
                loan_car_id=loan_car.id,
                loan_sale_id=loan_sale.id,
                title=title,
                message=message,
                notification_type='last_payment_received'
            )
            
            return notification
        
        except Exception as e:
            print(f"Error creating last payment notification: {e}")
            return None
    
    # @staticmethod
    # def create_overdue_payment_notification(loan_car, user_id, overdue_amount):
    #     """Create notification for overdue payments"""
        
    #     car = loan_car.car
        
    #     title = "Payment Overdue"
    #     message = f"Your payment for {car.make} {car.model} ({car.year}) is overdue. Amount due: ${overdue_amount:,.2f}. Please make your payment as soon as possible to avoid late fees."
        
    #     notification = LoanNotification(
    #         loan_car_id=loan_car.id,
    #         user_id=user_id,
    #         title=title,
    #         message=message,
    #         notification_type='payment_overdue'
    #     )
        
    #     db.session.add(notification)
    #     db.session.commit()
    #     return notification

# Usage examples:
# When loan car status changes to pending:
# LoanNotification.create_loan_status_notification(loan_car, user_id, 'pending')

# When loan car status changes to approved:
# LoanNotification.create_loan_status_notification(loan_car, user_id, 'approved')

# When payment is received:
# LoanNotification.create_payment_notification(payment, user_id)

# For overdue payments:
# LoanNotification.create_overdue_payment_notification(loan_car, user_id, overdue_amount)