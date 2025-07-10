from flask import Blueprint, jsonify, request
from flask_login import login_required
from models import db
from models.loan_car import LoanCar, LoanSale
from models.car import Car
import datetime
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

loan_api = Blueprint('loan_api', __name__, url_prefix='/api/loan')

@loan_api.route('/available-cars', methods=['GET'])

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
                'horsepower': car.horsepower,
                'mileage': car.mileage,
                'body_type': car.body_type,
                'transmission': car.transmission,
                'fuel_type': car.fuel_type,
                'seats': car.seats,
                'image_url': car.image_url,
                'license_plate': car.license_plate,
                'description': car.description,
                'loan_sale_price': float(loan_car.loan_sale_price),
                'commission_rate': float(loan_car.commission_rate),
                'date_offered': loan_car.date_offered.isoformat(),
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
    

@loan_api.route('/cars-loan-details/<int:car_id>', methods=['GET'])
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
            'horsepower': car.horsepower,
            'mileage': car.mileage,
            'body_type': car.body_type,
            'license_plate': car.license_plate,
            'loan_sale_price': float(loan.loan_sale_price),
            'description': car.description,
            'image_url': car.image_url,
            'interest_rate': float(loan.commission_rate),
            'date_offered': loan.date_offered.isoformat() if loan.date_offered else None,
        }

        return jsonify({'success': True, 'car': car_data})
    
    except Exception as e:
        print(f"Error in get_car: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch car details'
        }), 500
    

@loan_api.route('/set-pending/<int:car_id>', methods=['POST'])
def set_pending_status(car_id):
    
    try:
        
        data = request.get_json()
        if not data or 'car_id' not in data:
            return jsonify({'success': False, 'error': 'Invalid request data'}), 400
        
        if data.get('car_id') != car_id:
            return jsonify({'success': False, 'error': 'Car ID mismatch'}), 400
        
        loan_car = LoanCar.query.filter_by(car_id=car_id).first()
        if not loan_car:
            return jsonify({'success': False, 'error': 'LoanCar not found'}), 404
        
        if loan_car.status != 'available':
            return jsonify({
                'success': False, 
                'error': f'Cannot set to pending. Current status: {loan_car.status}'
            }), 400
        
        loan_car.status = 'pending'

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Database commit error: {str(e)}")
            return jsonify({
                'success': False, 
                'error': 'Failed to update loan status to pending'
            }), 500
        
        return jsonify({
            'success': True,
            'car_id': car_id,
            'new_status': loan_car.status,
            'message': 'Loan car status set to pending'
        })
    
    except Exception as e:
        print(f"Error in set-pending-status: {str(e)}")
        return jsonify({'success': False, 'error': 'Unexpected error', 'message': str(e)}), 500
        

@loan_api.route('/car-loan-status/<int:car_id>', methods=['POST'])

def update_status(car_id):

    try:
        loan_car = LoanCar.query.filter_by(car_id=car_id).first()
        if not loan_car:
            return jsonify({'success': False, 'error': 'LoanCar not found'}), 404
        
        if loan_car.status != 'pending':
            return jsonify({
                'success': False, 
                'error': f'Cannot update status. Current status: {loan_car.status}'
            }), 400

        data = request.get_json()
        if not data:
            return jsonify({'success':False, 'error': 'No data provided'}), 400
        
        if 'is_approved' not in data or 'car_id' not in data:
            return jsonify({'success': False, 'error': 'Invalid request data'}), 400

        is_approved = data.get('is_approved')
        get_car_id = data.get('car_id')

        if is_approved not in [True, False] or get_car_id != car_id:
            return jsonify({'success': False, 'error': 'Invalid request data'}), 400
        
        loan_car.status = 'approved' if is_approved else 'available'
        
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
        print(f"Error in updating status approval: {str(e)}")
        return jsonify({'success': False, 'error': 'Unexpected error', 'message': str(e)}), 500
    
    
#If the car loan is approved, this endpoint will activate the loan and set the status to active.
#It will also get the loan details and borrower information.
@loan_api.route('/activate-car-loan', methods=['POST'])

def activate_car_loan():
    
    try:
        
        data = request.get_json()
        if not data or 'car_id' not in data:
            return jsonify({'success': False, 'error': 'Invalid request data'}), 400
        
        car_id = data.get('car_id') 
        if not car_id:
            return jsonify({'success': False, 'error': 'Car ID is required'}), 400
        
        loan_car = LoanCar.query.filter_by(car_id=car_id).first()
        if not loan_car:    
            return jsonify({'success': False, 'error': 'LoanCar not found'}), 404
        
        if loan_car.status != 'approved':
            return jsonify({
                'success': False, 
                'error': f'Cannot activate loan car. Current status: {loan_car.status}'
            }), 400
            
        existing_loan_sale = LoanSale.query.filter_by(loan_car_id=loan_car.id).first()
        if existing_loan_sale:
            return jsonify({
                'success': False, 
                'error': 'Loan sale already exists for this car'
            }), 400
        
            
        try:
            response = requests.get(
                #f'https://api.example.com/active/{car_id}',
                f'http://localhost:5000/api/loan/fake-loan-data/{car_id}',
                timeout=5
            )
            
            if response.status_code != 200:
                return jsonify({
                    'success': False, 
                    'error': 'Failed to fetch car details from external API'
                }), 500
            
            data = response.json()
            if not data or 'loan_data' not in data:
                return jsonify({
                    'success': False, 
                    'error': 'Invalid response from external API'
                }), 500
            # Assuming the API returns user_data and loan_data in the response
            user_data = data.get('user_data')
            loan_data = data.get('loan_data')
            if not user_data or not loan_data:
                return jsonify({
                    'success': False, 
                    'error': 'Missing user or loan data in response from external API'
                }), 500
                
            
        except requests.RequestException as e:
            print(f"External API error: {str(e)}")
            return jsonify({'success': False, 'error': 'External service unavailable'}), 503
        except ValueError as e:
            print(f"API response parsing error: {str(e)}")
            return jsonify({'success': False, 'error': 'Invalid response from external service'}), 503
            
        
        loan_sale = LoanSale(
            loan_car_id=loan_car.id,
            borrower_name=user_data.get('first_name', '') + ' ' + user_data.get('last_name', ''),
            borrower_email=user_data.get('email', ''),
            borrower_phone=user_data.get('phone', ''),
            loan_term_months=loan_data.get('loan_term_months', 0),
            interest_rate=loan_data.get('interest_rate', 0.0),
            monthly_payment = (loan_car.loan_sale_price + (loan_car.loan_sale_price * loan_data.get('interest_rate', 0.0) / 100)) / loan_data.get('loan_term_months'),
            total_commission_expected = (loan_car.loan_sale_price + (loan_car.loan_sale_price * loan_data.get('interest_rate') / 100)),
            commission_received = 0.0,
            expected_monthly_commission = (loan_car.loan_sale_price + (loan_car.loan_sale_price * loan_data.get('interest_rate', 0.0) / 100)) / loan_data.get('loan_term_months')
            # remaining_balance = loan_sale.total_commission_expected - loan_sale.commission_received,
        )
        
        loan_car.status = 'active'
        loan_car.activated_at = datetime.datetime.utcnow()
        
        
        try:
            db.session.add(loan_sale)
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            print(f"Database commit error: {str(e)}")
            return jsonify({
                'success': False, 
                'error': 'Failed to activate car loan'
            }), 500
            
        return jsonify({
            'success': True,
            'car_id': car_id,
            'status': loan_car.status,
            'activated_at': loan_car.activated_at.isoformat(),
            'message': 'Car loan activated successfully'
        })
    except Exception as e:
        print(f"Error in activate_car_loan: {str(e)}")
        return jsonify({
            'success': False, 
            'error': 'Unexpected error', 
            'message': str(e)
        }), 500
        
        

# Will return all active loans with their details.
@loan_api.route('/get-active-loans', methods=['GET'])

def get_active_loans():
    
    try:
        active_loans = db.session.query(LoanCar, Car).join(Car).filter(
            LoanCar.status == 'active'
        ).all()
        
        loan_sale = db.session.query(LoanSale).filter(
            LoanSale.loan_car_id.in_([loan_car.id for loan_car, _ in active_loans])
        ).all()
        
        loans_data = []
        for loan_car, car in active_loans:
            loans_data.append({
                'id': loan_car.id,
                'car_id': car.id,
                'car_details': {
                    'id': car.id,
                    'make': car.make,
                    'model': car.model,
                    'year': car.year,
                    'color': car.color,
                    'horsepower': car.horsepower,
                    'mileage': car.mileage,
                    'body_type': car.body_type,
                    'transmission': car.transmission,
                    'fuel_type': car.fuel_type,
                    'seats': car.seats,
                    'image_url': car.image_url,
                    'license_plate': car.license_plate,
                    'description': car.description
                },
                'borrower_info': {
                    'id': loan_sale.id,
                    'name': loan_sale.borrower_name,
                    'email': loan_sale.borrower_email,
                    'phone': loan_sale.borrower_phone
                },
                'loan_details': {
                    'loan_amount': float(loan_car.loan_sale_price),
                    'loan_term': loan_sale.loan_term_months,
                    'interest_rate': float(loan_sale.interest_rate),
                },
                'status': loan_car.status,
                'activated_at': loan_car.activated_at.isoformat() if loan_car.activated_at else None,
                'date_offered': loan_car.date_offered.isoformat() if loan_car.date_offered else None,
            })
            
        return jsonify({
            'success': True,
            'active_loans': loans_data,
            'total': len(loans_data)
        })
    except Exception as e:
        print(f"Error in get_active_loans: {str(e)}")
        return jsonify({
            'success': False, 
            'error': 'Failed to fetch active loans',
            'message': str(e)
        }), 500
        
# This endpoint will return all loans for a specific user.
@loan_api.route('/get-loan-by-user/<int:user_id>', methods=['GET'])

def get_loan_by_user(user_id):
    try:
        user_loans = db.session.query(LoanCar, Car).join(Car).filter(
            LoanCar.borrower_id == user_id,
            LoanCar.status.in_(['active'])
        ).all()
        
        loan_sale = db.session.query(LoanSale).filter(
            LoanSale.loan_car_id.in_([loan_car.id for loan_car, _ in user_loans])  
        ).all()
        
        if not user_loans:
            return jsonify({'success': False, 'error': 'No active loans found for this user'}), 404
        
        loans_data = []
        for loan_car, car in user_loans:
            loans_data.append({
                'id': loan_car.id,
                'car_id': car.id,
                'car_details': {
                    'make': car.make,
                    'model': car.model,
                    'year': car.year,
                    'color': car.color,
                    'horsepower': car.horsepower,
                    'mileage': car.mileage,
                    'body_type': car.body_type,
                    'transmission': car.transmission,
                    'fuel_type': car.fuel_type,
                    'seats': car.seats,
                    'image_url': car.image_url,
                    'license_plate': car.license_plate,
                    'description': car.description
                },
                'loan_details': {
                    'loan_amount': float(loan_car.loan_sale_price),
                    'loan_term': loan_sale.loan_term_months,
                    'interest_rate': float(loan_car.interest_rate),
                },
                'status': loan_car.status,
                'activated_at': loan_car.activated_at.isoformat() if loan_car.activated_at else None,
                'date_offered': loan_car.date_offered.isoformat() if loan_car.date_offered else None,
            })
            
        return jsonify({
            'success': True,
            'user_loans': loans_data,
            'total': len(loans_data)
        })
        
    except Exception as e:
        print(f"Error in get_loan_by_user: {str(e)}")
        return jsonify({
            'success': False, 
            'error': 'Failed to fetch user loans',
            'message': str(e)
        }), 500
        

@loan_api.route('/receive-monthly-commission/<int:loan_car_id>', methods=['POST'])
def receive_monthly_commission(loan_car_id):
    try:
        loan_car = LoanCar.query.get(loan_car_id)
        if not loan_car:
            return jsonify({'success': False, 'error': 'LoanCar not found'}), 404
        
        loan_sale = LoanSale.query.filter_by(loan_car_id=loan_car_id).first()
        if not loan_sale:
            return jsonify({'success': False, 'error': 'LoanSale not found'}), 404


        
        if loan_car.status != 'active':
            return jsonify({
                'success': False, 
                'error': f'Cannot receive commission. Current status: {loan_car.status}'
            }), 400
        
        data = request.get_json()
        if not data or 'commission_amount' not in data:
            return jsonify({'success': False, 'error': 'Invalid request data'}), 400
        
        car_id = data.get('car_id')
        if not car_id or car_id != loan_car.car_id:
            return jsonify({'success': False, 'error': 'Car ID mismatch'}), 400
        
        borrower_id = data.get('id')
        if not borrower_id or borrower_id != loan_sale.id:
            return jsonify({'success': False, 'error': 'Borrower ID mismatch'}), 400
        
        monthly_commission_amount = data.get('commission_amount')
        if not isinstance(monthly_commission_amount, (int, float)):
            return jsonify({'success': False, 'error': 'Invalid commission amount'}), 400
        
        expected_commission_per_month = (loan_car.loan_sale_price + (loan_car.loan_sale_price * loan_sale.interest_rate / 100)) / loan_sale.loan_term_months
        
        total_commission_expected = (loan_car.loan_sale_price + (loan_car.loan_sale_price * loan_sale.interest_rate / 100))
        
        if monthly_commission_amount < expected_commission_per_month:
            return jsonify({
                'success': False, 
                'error': f'Monthly commission amount must be at least {expected_commission_per_month}'
            }), 400
        
        loan_sale.expected_monthly_commission = expected_commission_per_month
        loan_sale.total_commission_expected = total_commission_expected
        loan_sale.commission_received += monthly_commission_amount
        loan_sale.date_commission_received = datetime.datetime.utcnow()
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Database commit error: {str(e)}")
            return jsonify({
                'success': False, 
                'error': 'Failed to process commission payment'
            }), 500
        return jsonify({
            'success': True,
            'loan_car_id': loan_car_id,
            'car_id': loan_car.car_id,
            'commission_received': loan_sale.commission_received,
            'date_commission_received': loan_sale.date_commission_received.isoformat() if loan_sale.date_commission_received else None,
            'message': 'Commission payment processed successfully'
        })
    except Exception as e:
        print(f"Error in receive_monthly_commission: {str(e)}")
        return jsonify({
            'success': False, 
            'error': 'Unexpected error', 
            'message': str(e)
        }), 500

@loan_api.route('/set-status-to-paid/<int:loan_car_id>', methods=['POST'])
def set_status_to_paid(loan_car_id):
    try:
        
        data = request.get_json()
        if not data or 'car_id' not in data:
            return jsonify({'success': False, 'error': 'Invalid request data'}), 400
        
        car_id = data.get('car_id')
        if not car_id:
            return jsonify({'success': False, 'error': 'Car ID is required'}), 400
        
        if car_id != loan_car_id:
            return jsonify({'success': False, 'error': 'Car ID mismatch'}), 400
        
        
        loan_car = LoanCar.query.get(loan_car_id)
        if not loan_car:
            return jsonify({'success': False, 'error': 'LoanCar not found'}), 404
        
        if loan_car.status != 'active':
            return jsonify({
                'success': False, 
                'error': f'Cannot set status to paid. Current status: {loan_car.status}'
            }), 400
        
        loan_sale = LoanSale.query.filter_by(loan_car_id=loan_car_id).first()
        if not loan_sale:
            return jsonify({'success': False, 'error': 'LoanSale not found'}), 404
        
        if loan_sale.commission_received <= loan_sale.total_commission_expected:
            return jsonify({
                'success': False, 
                'error': 'Commission not fully received'
            }), 400
        
        loan_car.status = 'paid'
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Database commit error: {str(e)}")
            return jsonify({
                'success': False, 
                'error': 'Failed to update loan status to paid'
            }), 500
        
        return jsonify({
            'success': True,
            'loan_car_id': loan_car_id,
            'new_status': loan_car.status,
            'message': 'Loan car status set to paid'
        })
    
    except Exception as e:
        print(f"Error in set_status_to_paid: {str(e)}")
        return jsonify({'success': False, 'error': 'Unexpected error', 'message': str(e)}), 500