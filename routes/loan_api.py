from flask import Blueprint, jsonify
from flask_login import login_required
from models import db
from models.loan_car import LoanCar
from models.car import Car
import requests 
from requests.exceptions import RequestException, Timeout, ConnectionError

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
                'loan_sale_price': float(loan_car.loan_sale_price),
                'commission_rate': float(loan_car.commission_rate),
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
        print(f"Error in get_available_cars: {str(e)}")
        return jsonify({
            'success': False, 
            'error': 'Failed to fetch available cars',
            'message': str(e)
        }), 500
    

@loan_api.route('/cars-in-loan/<int:car_id>', methods=['GET'])
@login_required
def get_car(car_id):
    
    try: 
        loan_car = db.session.query(LoanCar, Car).join(Car).filter(Car.id == car_id).first()

        if not loan_car:
            return jsonify({'success': False, 'error': 'Car not found'}), 404
        
        loan, car = loan_car

        car_data = {
            'id': loan.id,
            'car_id': car.id,
            'make': car.make,
            'model': car.model,
            'year': car.year,
            'color': car.color,
            'license_plate': car.license_plate,
            'loan_sale_price': float(loan.loan_sale_price),
            'description': car.description,
            'image_url': car.image_url
        }

        return jsonify({'success': True, 'car': car_data})
    
    except Exception as e:
        print(f"Error in get_car: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch car details'
        }), 500
    
@loan_api.route('/loan-car-status/<int:car_id>', methods=['GET'])
@login_required
def get_status(car_id):

    try:
        loan_car = LoanCar.query.filter_by(car_id=car_id).first()
        if not loan_car:
            return jsonify({'success': False, 'error': 'LoanCar not found'}), 404
        
        if loan_car.status != 'pending':
            return jsonify({
                'success': False, 
                'error': f'Cannot update status. Current status: {loan_car.status}'
            }), 400

        try:
            response = requests.get(
                f"https://api.example.com/approval/{car_id}",
                timeout=10
            )
        except (ConnectionError, Timeout) as e:
            print(f"API connection error: {str(e)}")
            return jsonify({
                'success': False, 
                'error': 'Failed to connect to loan management system'
            }), 502
        except RequestException as e:
            print(f"API request error: {str(e)}")
            return jsonify({
                'success': False, 
                'error': 'Error communicating with loan management system'
            }), 502
        
        if response.status_code != 200:
            return jsonify({
                'success': False, 
                'error': 'Failed to fetch data from external API'
            }), 502
        

        data = response.json()
        approved = data.get('approved')
        get_car_id = data.get('car_id')

        if(approved not in [True, False] or get_car_id != car_id):
            return jsonify({'success': False, 'error': 'Invalid response from loan management system'}), 400

        loan_car.status = 'active' if approved else 'rejected'
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Database commit error: {str(e)}")
            return jsonify({
                'success': False, 
                'error': 'Failed to update loan status'
            }), 500

        return jsonify({
            'success': True,
            'car_id': car_id,
            'new_status': loan_car.status
        })
    
    except Exception as e:
        print(f"Error in fetching status approval: {str(e)}")
        return jsonify({'success': False, 'error': 'Unexpected error', 'message': str(e)}), 500
    