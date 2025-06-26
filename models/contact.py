from datetime import datetime
from models import db

class ContactMessage(db.Model):
    """Model for storing contact form messages"""
    __tablename__ = 'contact_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    admin_reply = db.Column(db.Text, nullable=True)
    replied_at = db.Column(db.DateTime, nullable=True)
    replied_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationship with User model (admin who replied)
    admin = db.relationship('User', backref='replied_messages', foreign_keys=[replied_by])
    
    def __repr__(self):
        return f"<ContactMessage {self.id} from {self.name}>" 