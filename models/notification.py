from models import db
from datetime import datetime

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(20), nullable=False)  # 'booking_status', 'payment', 'system', etc.
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define relationship with User
    user = db.relationship('User', backref=db.backref('notifications', lazy=True))
    # Define relationship with Booking (if related to a booking)
    booking = db.relationship('Booking', backref=db.backref('notifications', lazy=True))
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.title}>'
    
    @staticmethod
    def create_booking_notification(user_id, booking_id, booking_status, booking_reference=None):
        """
        Create a notification based on booking status change
        
        Args:
            user_id (int): ID of the user to notify
            booking_id (int): ID of the booking
            booking_status (str): New status of the booking
            booking_reference (str, optional): Booking reference number
        """
        status_messages = {
            'pending': {
                'title': 'Booking Received',
                'message': f'Your booking #{booking_reference} has been received and is pending payment confirmation.'
            },
            'confirmed': {
                'title': 'Booking Confirmed',
                'message': f'Good news! Your booking #{booking_reference} has been confirmed.'
            },
            'completed': {
                'title': 'Booking Completed',
                'message': f'Your booking #{booking_reference} has been marked as completed. Thank you for choosing JDM Car Rentals!'
            },
            'cancelled': {
                'title': 'Booking Cancelled',
                'message': f'Your booking #{booking_reference} has been cancelled. If you have any questions, please contact our support team.'
            }
        }
        
        if booking_status in status_messages:
            notification = Notification(
                user_id=user_id,
                booking_id=booking_id,
                title=status_messages[booking_status]['title'],
                message=status_messages[booking_status]['message'],
                notification_type='booking_status'
            )
            db.session.add(notification)
            try:
                db.session.commit()
                return notification
            except Exception as e:
                db.session.rollback()
                print(f"Error creating notification: {str(e)}")
                return None
        return None
    
    @staticmethod
    def create_payment_notification(user_id, booking_id, payment_status, amount, booking_reference=None):
        """
        Create a notification about payment status
        
        Args:
            user_id (int): ID of the user to notify
            booking_id (int): ID of the booking
            payment_status (str): Payment status ('completed', 'failed', etc.)
            amount (float): Payment amount
            booking_reference (str, optional): Booking reference number
        """
        formatted_amount = "{:.2f}".format(amount)
        
        if payment_status == 'completed':
            notification = Notification(
                user_id=user_id,
                booking_id=booking_id,
                title='Payment Successful',
                message=f'Your payment of ₱{formatted_amount} for booking #{booking_reference} was successful.',
                notification_type='payment'
            )
        elif payment_status == 'failed':
            notification = Notification(
                user_id=user_id,
                booking_id=booking_id,
                title='Payment Failed',
                message=f'Your payment of ₱{formatted_amount} for booking #{booking_reference} failed. Please try again.',
                notification_type='payment'
            )
        elif payment_status == 'refunded':
            notification = Notification(
                user_id=user_id,
                booking_id=booking_id,
                title='Payment Refunded',
                message=f'Your payment of ₱{formatted_amount} for booking #{booking_reference} has been refunded.',
                notification_type='payment'
            )
        else:
            notification = Notification(
                user_id=user_id,
                booking_id=booking_id,
                title='Payment Update',
                message=f'There has been an update to your payment for booking #{booking_reference}. Status: {payment_status}',
                notification_type='payment'
            )
        
        db.session.add(notification)
        try:
            db.session.commit()
            return notification
        except Exception as e:
            db.session.rollback()
            print(f"Error creating notification: {str(e)}")
            return None
    
    @staticmethod
    def get_unread_count(user_id):
        """Get count of unread notifications for a user"""
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()
    
    @staticmethod
    def create_admin_booking_notification(booking_id, user_name, car_name, booking_reference=None):
        """
        Create notifications for all admin users when a new booking is made
        
        Args:
            booking_id (int): ID of the booking
            user_name (str): Name of the user who made the booking
            car_name (str): Name of the car that was booked
            booking_reference (str, optional): Booking reference number
        """
        from models.user import User
        
        # Find all admin users
        admin_users = User.query.filter_by(is_admin=True).all()
        
        if not admin_users:
            print("No admin users found")
            return False
        
        # Create a notification for each admin
        for admin in admin_users:
            notification = Notification(
                user_id=admin.id,
                booking_id=booking_id,
                title='New Booking Received',
                message=f'A new booking (#{booking_reference}) has been made by {user_name} for the {car_name}.',
                notification_type='booking_status'
            )
            db.session.add(notification)
        
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin notifications: {str(e)}")
            return False
            
    @staticmethod
    def create_admin_return_notification(booking_id, user_name, car_name, booking_reference=None):
        """
        Create notifications for all admin users when a car is returned
        
        Args:
            booking_id (int): ID of the booking
            user_name (str): Name of the user who returned the car
            car_name (str): Name of the car that was returned
            booking_reference (str, optional): Booking reference number
        """
        from models.user import User
        
        # Find all admin users
        admin_users = User.query.filter_by(is_admin=True).all()
        
        if not admin_users:
            print("No admin users found")
            return False
        
        # Create a notification for each admin
        for admin in admin_users:
            notification = Notification(
                user_id=admin.id,
                booking_id=booking_id,
                title='Car Returned',
                message=f'Car return request received for booking #{booking_reference}. {user_name} has returned the {car_name}.',
                notification_type='booking_status'
            )
            db.session.add(notification)
        
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin return notifications: {str(e)}")
            return False
    
    @staticmethod
    def create_admin_payment_notification(booking_id, user_name, amount, payment_type, booking_reference=None):
        """
        Create notifications for all admin users when a payment is made
        
        Args:
            booking_id (int): ID of the booking
            user_name (str): Name of the user who made the payment
            amount (float): Payment amount
            payment_type (str): Type of payment ('booking' or 'late_fee')
            booking_reference (str, optional): Booking reference number
        """
        from models.user import User
        
        # Find all admin users
        admin_users = User.query.filter_by(is_admin=True).all()
        
        if not admin_users:
            print("No admin users found")
            return False
        
        formatted_amount = "{:.2f}".format(amount)
        payment_desc = "late fee" if payment_type == 'late_fee' else "booking"
        
        # Create a notification for each admin
        for admin in admin_users:
            notification = Notification(
                user_id=admin.id,
                booking_id=booking_id,
                title='Payment Received',
                message=f'A payment of ₱{formatted_amount} for {payment_desc} #{booking_reference} has been made by {user_name}.',
                notification_type='payment'
            )
            db.session.add(notification)
        
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin payment notifications: {str(e)}")
            return False
    
    @staticmethod
    def create_admin_profile_notification(user_id, user_name, field_changed):
        """
        Create notifications for all admin users when a user updates their profile
        
        Args:
            user_id (int): ID of the user who updated their profile
            user_name (str): Name of the user who updated their profile
            field_changed (str): Description of what was changed
        """
        from models.user import User
        
        # Find all admin users
        admin_users = User.query.filter_by(is_admin=True).all()
        
        if not admin_users:
            print("No admin users found")
            return False
        
        # Create a notification for each admin
        for admin in admin_users:
            notification = Notification(
                user_id=admin.id,
                title='User Profile Updated',
                message=f'User {user_name} has updated their profile: {field_changed}.',
                notification_type='system'
            )
            db.session.add(notification)
        
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin profile update notifications: {str(e)}")
            return False
            
    @staticmethod
    def create_admin_notification(title, message, notification_type='system', booking_id=None):
        """
        Create a generic notification for all admin users
        
        Args:
            title (str): Notification title
            message (str): Notification message
            notification_type (str): Type of notification (default: 'system')
            booking_id (int, optional): ID of the related booking, if any
        """
        from models.user import User
        
        # Find all admin users
        admin_users = User.query.filter_by(is_admin=True).all()
        
        if not admin_users:
            print("No admin users found")
            return False
        
        # Create a notification for each admin
        for admin in admin_users:
            notification = Notification(
                user_id=admin.id,
                booking_id=booking_id,
                title=title,
                message=message,
                notification_type=notification_type
            )
            db.session.add(notification)
        
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin notifications: {str(e)}")
            return False
    
    @staticmethod
    def create_damage_fee_notification(user_id, booking_id, amount, damage_description, booking_reference=None):
        """
        Create a notification about damage fees
        
        Args:
            user_id (int): ID of the user to notify
            booking_id (int): ID of the booking
            amount (float): Damage fee amount
            damage_description (str): Description of the damage
            booking_reference (str, optional): Booking reference number
        """
        formatted_amount = "{:.2f}".format(amount)
        
        notification = Notification(
            user_id=user_id,
            booking_id=booking_id,
            title='Damage Fee Charged',
            message=f'A damage fee of ₱{formatted_amount} has been charged for booking #{booking_reference} due to: {damage_description}',
            notification_type='payment'
        )
        
        db.session.add(notification)
        try:
            db.session.commit()
            return notification
        except Exception as e:
            db.session.rollback()
            print(f"Error creating damage fee notification: {str(e)}")
            return None
            
    @staticmethod
    def create_admin_damage_notification(booking_id, user_name, amount, damage_description, booking_reference=None):
        """
        Create notifications for all admin users about damage charges
        
        Args:
            booking_id (int): ID of the booking
            user_name (str): Name of the user being charged
            amount (float): Damage fee amount
            damage_description (str): Description of the damage
            booking_reference (str, optional): Booking reference number
        """
        from models.user import User
        
        # Find all admin users
        admin_users = User.query.filter_by(is_admin=True).all()
        
        if not admin_users:
            print("No admin users found")
            return False
        
        formatted_amount = "{:.2f}".format(amount)
        
        # Create a notification for each admin
        for admin in admin_users:
            notification = Notification(
                user_id=admin.id,
                booking_id=booking_id,
                title='Damage Fee Charged',
                message=f'A damage fee of ₱{formatted_amount} has been charged to {user_name} for booking #{booking_reference}. Damage: {damage_description}',
                notification_type='payment'
            )
            db.session.add(notification)
        
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin damage fee notifications: {str(e)}")
            return False 