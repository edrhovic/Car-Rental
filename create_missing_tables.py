from app import app, db
from models.contact import ContactMessage

with app.app_context():
    # Create all tables that don't exist yet
    db.create_all()
    print("Missing tables have been created successfully!") 