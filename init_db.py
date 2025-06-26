"""
Database initialization script using Flask-Migrate
This script should be used after you've manually created the database in MySQL Workbench
"""

from app import app, db
from models.user import User
from models.car import Car
from models.booking import Booking
from models.review import Review
from models.payment import Payment
from flask_migrate import Migrate, init, migrate, upgrade
import os

# Initialize Flask-Migrate
migrate = Migrate(app, db)

def init_db():
    """Initialize the database with Flask-Migrate"""
    # Create the migrations directory
    init()
    
    # Create a migration
    migrate()
    
    # Apply the migration
    upgrade()
    
    print("Database tables created successfully!")

if __name__ == '__main__':
    # Check if the database already exists
    try:
        # Try a simple query
        db.session.execute('SELECT 1')
        print("Database already exists!")
    except:
        # If the query fails, initialize the database
        print("Initializing database...")
        init_db() 