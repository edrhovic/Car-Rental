# Routes package initialization 

# Import all blueprints
from routes.admin import admin
from routes.auth import auth
from routes.notification import notification_bp
from routes.user import user
from routes.contact import contact_bp
from routes.car import car
from routes.booking import booking
from routes.loan_api import loan_api

# Expose blueprints
__all__ = ['admin', 'auth', 'notification_bp', 'user', 'contact_bp', 'car', 'booking', 'loan_api'] 