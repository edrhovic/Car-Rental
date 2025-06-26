from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import db
from models.loan_car import LoanCar
from models.car import Car

loan_api = Blueprint('loan_api', __name__, url_prefix='/api/loan')

@loan_api.route('/available-cars', methods=['GET'])
@login_required
def get_available_cars():
    """API endpoint for loan management system to fetch available cars"""
    try:
        loan_cars = db.session.query(LoanCar, Car).join(Car).filter(
            LoanCar.status == 'available'
        ).all()
        
        cars_data = []
        for loan_car, car in loan_cars:
            cars_data.append({
                'id': loan_car.id,
                'car_id': car.id,
                'make': car.make,
                'model': car.model,
                'year': car.year,
                'color': car.color,
                'license_plate': car.license_plate,
                'loan_sale_price': loan_car.loan_sale_price,
                'commission_rate': loan_car.commission_rate,
                'date_offered': loan_car.date_offered.isoformat(),
                'description': car.description,
                'image_url': car.image_url
            })
        
        return jsonify({
            'success': True,
            'cars': cars_data,
            'total': len(cars_data)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
