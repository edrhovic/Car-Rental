from datetime import datetime
from models import db

class PageContent(db.Model):
    __tablename__ = 'page_contents'
    
    id = db.Column(db.Integer, primary_key=True)
    page_name = db.Column(db.String(50), nullable=False, unique=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __repr__(self):
        return f'<PageContent {self.page_name}>' 