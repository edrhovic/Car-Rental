from flask import Blueprint, jsonify, request
from flask_login import login_required
from models import db
from models.loan_car import LoanCar, LoanSale, LoanPayment
from models.car import Car
import datetime
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError
from sqlalchemy import func

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
def approve_status(car_id):
    try:
        loan_car = LoanCar.query.filter_by(car_id=car_id).first()
        if not loan_car:
            return jsonify({'success': False, 'error': 'Loan Car not found'}), 404

        data = request.get_json()
        if not data or 'is_approved' not in data or 'car_id' not in data:
            return jsonify({'success': False, 'error': 'Invalid data'}), 400

        if data.get('car_id') != car_id:
            return jsonify({'success': False, 'error': 'Car ID mismatch'}), 400

        is_approved = data.get('is_approved')
        disbursement_id = data.get('disbursement_id')

        if is_approved:
            user_id = data.get('user_id')
            first_name = data.get('first_name')
            middle_name = data.get('middle_name')
            last_name = data.get('last_name')
            email = data.get('email')
            contact = data.get('contact')

            required_fields = [user_id, first_name, last_name, email, contact, disbursement_id]
            if any(field is None for field in required_fields):
                return jsonify({'success': False, 'error': 'Missing required user or disbursement information'}), 400

            try:
                loan_sale = LoanSale(
                    disbursement_id=disbursement_id,
                    loan_car_id=int(car_id),
                    user_id=int(user_id),
                    first_name=first_name,
                    middle_name=middle_name,
                    last_name=last_name,
                    email=email,
                    contact=contact
                )
                loan_car.status = 'active'
                loan_car.activated_at = datetime.datetime.utcnow()

                db.session.add(loan_sale)
                db.session.commit()
            except Exception as db_exc:
                db.session.rollback()
                print(f"Database error in approve_status: {str(db_exc)}")
                return jsonify({'success': False, 'error': 'Database error', 'message': str(db_exc)}), 500

            return jsonify({
                'success': True,
                'new_loan_car_status': loan_car.status,
                'approved_at': loan_car.activated_at.isoformat() if loan_car.activated_at else None,
                'disbursement_id': disbursement_id
            })
        else:
            loan_car.status = 'available'
            loan_car.is_available = True
            
            db.session.commit()
            return jsonify({'success': False, 'error': 'Loan not approved'}), 400

    except Exception as e:
        print(f"Error in approve_status: {str(e)}")
        return jsonify({'success': False, 'error': 'Error in updating loan status', 'message': str(e)}), 500
    
        

@loan_api.route('/receive-monthly-commission', methods=['POST'])
def receive_monthly_commission():
    try:
        data = request.get_json()
        if not data or 'commission_amount' not in data or 'car_id' not in data:
            return jsonify({'success': False, 'error': 'Missing required data'}), 400
        
        car_id = data.get('car_id')
        disbursement_id = data.get('disbursement_id')
        monthly_commission_amount = data.get('commission_amount')
        
        if not isinstance(monthly_commission_amount, (int, float)) or monthly_commission_amount <= 0:
            return jsonify({'success': False, 'error': 'Invalid commission amount'}), 400
        
        loan_car = LoanCar.query.filter_by(car_id=car_id).first()
        
        if not loan_car:
            return jsonify({'success': False, 'error': 'LoanCar not found'}), 404
        
        if loan_car.status != 'active':
            return jsonify({'success': False, 'error': f'Cannot receive commission. Current status: {loan_car.status}'}), 400
        
        loan_sale = LoanSale.query.filter_by(loan_car_id=loan_car.id).first()
        
        if not loan_sale:
            return jsonify({'success': False, 'error': 'LoanSale not found'}), 404
        
        if disbursement_id and loan_sale.disbursement_id != disbursement_id:
            return jsonify({'success': False, 'error': 'Disbursement ID mismatch'}), 400
        
        total_commission_expected = loan_car.loan_sale_price + (loan_car.loan_sale_price * loan_car.commission_rate / 100)
        
        loan_payment = LoanPayment.query.filter_by(disbursement_id=loan_sale.id).first()
        
        if not loan_payment:
            loan_payment = LoanPayment(
                disbursement_id=loan_sale.id,
                total_commission_expected=total_commission_expected,
                commission_received=0.0
            )
            db.session.add(loan_payment)
        
        new_total_received = (loan_payment.commission_received or 0) + monthly_commission_amount
        
        if new_total_received > total_commission_expected:
            return jsonify({
                'success': False,
                'error': f'Commission amount exceeds remaining balance. Expected: {total_commission_expected}, Already received: {loan_payment.commission_received or 0}'
            }), 400
        
        loan_payment.total_commission_expected = total_commission_expected
        loan_payment.commission_received = new_total_received
        loan_payment.date_commission_received = datetime.datetime.utcnow()
        
        if new_total_received >= total_commission_expected:
            loan_car.status = 'paid'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'disbursement_id': loan_sale.disbursement_id,
            'car_id': car_id,
            'commission_received': loan_payment.commission_received,
            'total_commission_expected': total_commission_expected,
            'date_commission_received': loan_payment.date_commission_received.isoformat(),
            'message': 'Commission payment processed successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Unexpected error occurred'
        }), 500
        
        
@loan_api.route('/get-total-commissions', methods=['POST'])
def get_total_commissions():
    try:
        data = request.get_json()
        if not data or 'disbursement_id' not in data or 'car_id' not in data:
            return jsonify({'success': False, 'error': 'Missing disbursement_id or car_id'}), 400

        disbursement_id = data.get('disbursement_id')
        car_id = data.get('car_id')

        loan_car = LoanCar.query.filter_by(car_id=car_id).first()
        if not loan_car:
            return jsonify({'success': False, 'error': 'LoanCar not found'}), 404

        loan_sale = LoanSale.query.filter_by(loan_car_id=loan_car.id, disbursement_id=disbursement_id).first()
        if not loan_sale:
            return jsonify({'success': False, 'error': 'LoanSale not found'}), 404

        loan_payment = LoanPayment.query.filter_by(disbursement_id=loan_sale.id).first()
        total_commission = loan_payment.commission_received

        return jsonify({
            'success': True,
            'disbursement_id': disbursement_id,
            'car_id': car_id,
            'total_commission': total_commission
        })
    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to fetch commission data', 'message': str(e)}), 500

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


@loan_api.route('/all-cars', methods=['GET'])
def get_all_cars():
    
    all_cars = Car.query.all()
    
    car_list = []
    
    for car in all_cars:
        car_list.append({
            'id': car.id,
            'make': car.make,
            'model': car.model,
            'year': car.year,
            'color': car.color
        })
        
    return jsonify({
        'success': True,
        'cars': car_list
    })

# @loan_api.route('/get-active-loans', methods=['GET'])

# def get_active_loans():
    
#     try:
#         active_loans = db.session.query(LoanCar, Car).join(Car).filter(
#             LoanCar.status == 'active'
#         ).all()
        
#         loan_sale = db.session.query(LoanSale).filter(
#             LoanSale.loan_car_id.in_([loan_car.id for loan_car, _ in active_loans])
#         ).all()
        
#         loans_data = []
#         for loan_car, car in active_loans:
#             loans_data.append({
#                 'id': loan_car.id,
#                 'car_id': car.id,
#                 'car_details': {
#                     'id': car.id,
#                     'make': car.make,
#                     'model': car.model,
#                     'year': car.year,
#                     'color': car.color,
#                     'horsepower': car.horsepower,
#                     'mileage': car.mileage,
#                     'body_type': car.body_type,
#                     'transmission': car.transmission,
#                     'fuel_type': car.fuel_type,
#                     'seats': car.seats,
#                     'image_url': car.image_url,
#                     'license_plate': car.license_plate,
#                     'description': car.description
#                 },
#                 'borrower_info': {
#                     'id': loan_sale.id,
#                     'name': loan_sale.borrower_name,
#                     'email': loan_sale.borrower_email,
#                     'phone': loan_sale.borrower_phone
#                 },
#                 'loan_details': {
#                     'loan_amount': float(loan_car.loan_sale_price),
#                     'loan_term': loan_sale.loan_term_months,
#                     'interest_rate': float(loan_sale.interest_rate),
#                 },
#                 'status': loan_car.status,
#                 'activated_at': loan_car.activated_at.isoformat() if loan_car.activated_at else None,
#                 'date_offered': loan_car.date_offered.isoformat() if loan_car.date_offered else None,
#             })
            
#         return jsonify({
#             'success': True,
#             'active_loans': loans_data,
#             'total': len(loans_data)
#         })
#     except Exception as e:
#         print(f"Error in get_active_loans: {str(e)}")
#         return jsonify({
#             'success': False, 
#             'error': 'Failed to fetch active loans',
#             'message': str(e)
#         }), 500
        
# # This endpoint will return all loans for a specific user.
# @loan_api.route('/get-loan-by-user/<int:user_id>', methods=['GET'])

# def get_loan_by_user(user_id):
#     try:
#         user_loans = db.session.query(LoanCar, Car).join(Car).filter(
#             LoanCar.borrower_id == user_id,
#             LoanCar.status.in_(['active'])
#         ).all()
        
#         loan_sale = db.session.query(LoanSale).filter(
#             LoanSale.loan_car_id.in_([loan_car.id for loan_car, _ in user_loans])  
#         ).all()
        
#         if not user_loans:
#             return jsonify({'success': False, 'error': 'No active loans found for this user'}), 404
        
#         loans_data = []
#         for loan_car, car in user_loans:
#             loans_data.append({
#                 'id': loan_car.id,
#                 'car_id': car.id,
#                 'car_details': {
#                     'make': car.make,
#                     'model': car.model,
#                     'year': car.year,
#                     'color': car.color,
#                     'horsepower': car.horsepower,
#                     'mileage': car.mileage,
#                     'body_type': car.body_type,
#                     'transmission': car.transmission,
#                     'fuel_type': car.fuel_type,
#                     'seats': car.seats,
#                     'image_url': car.image_url,
#                     'license_plate': car.license_plate,
#                     'description': car.description
#                 },
#                 'loan_details': {
#                     'loan_amount': float(loan_car.loan_sale_price),
#                     'loan_term': loan_sale.loan_term_months,
#                     'interest_rate': float(loan_car.interest_rate),
#                 },
#                 'status': loan_car.status,
#                 'activated_at': loan_car.activated_at.isoformat() if loan_car.activated_at else None,
#                 'date_offered': loan_car.date_offered.isoformat() if loan_car.date_offered else None,
#             })
            
#         return jsonify({
#             'success': True,
#             'user_loans': loans_data,
#             'total': len(loans_data)
#         })
        
#     except Exception as e:
#         print(f"Error in get_loan_by_user: {str(e)}")
#         return jsonify({
#             'success': False, 
#             'error': 'Failed to fetch user loans',
#             'message': str(e)
#         }), 500