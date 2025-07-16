from flask import Blueprint, jsonify, request
from flask_login import login_required
from models import db
from models.loan_car import LoanCar, LoanSale, LoanPayment, LoanNotification
from models.car import Car
import datetime
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError
from sqlalchemy import func
from decimal import Decimal, ROUND_HALF_UP

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
        
        car_id = data.get('car_id')
        
        if car_id != car_id:
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
        loan_notification = LoanNotification.create_loan_status_notification(loan_car, 'pending')

        try:
            db.session.add(loan_notification)
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
        
        loan_notif = LoanNotification.query.filter_by(loan_car_id=car_id).first()
        

        data = request.get_json()
        if not data or 'is_approved' not in data or 'car_id' not in data:
            return jsonify({'success': False, 'error': 'Invalid data'}), 400

        if data.get('car_id') != car_id:
            return jsonify({'success': False, 'error': 'Car ID mismatch'}), 400
        
        if loan_car.status == 'active':
            return jsonify({'success': True, 'error': f'Cannot update loan car status. Current status: {loan_car.status}'})

        is_approved = data.get('is_approved')
        disbursement_id = data.get('disbursement_id')

        if is_approved:
            user_id = data.get('user_id')
            first_name = data.get('first_name')
            middle_name = data.get('middle_name')
            last_name = data.get('last_name')
            email = data.get('email')
            contact = data.get('contact')
            loan_term = data.get('loan_term')
            birthdate = data.get('birthdate')
            gender = data.get('gender')
            marital_status = data.get('marital_status')
            city = data.get('city')
            complete_address = data.get('complete_address')
            company_name = data.get('company_name')
            job_title = data.get('job_title')
            employment_type = data.get('employment_type')
            years_employed = data.get('years_employed')
            monthly_income = data.get('monthly_income')
            other_income = data.get('other_income')
            existing_loans = data.get('existing_loans')
            user_front_id = data.get('front')
            user_back_id = data.get('back')
            

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
                    contact=contact,
                    loan_term=loan_term,
                    birthdate=birthdate,
                    gender=gender,
                    marital_status=marital_status,
                    city=city,
                    complete_address=complete_address,
                    company_name=company_name,
                    job_title=job_title,
                    employment_type=employment_type,
                    years_employed=years_employed,
                    monthly_income=monthly_income,
                    other_income=other_income,
                    existing_loans=existing_loans,
                    user_front_id=user_front_id,
                    user_back_id=user_back_id
                )
                
                loan_notification = LoanNotification.create_loan_status_notification(loan_car, 'approved')
                loan_car.status = 'active'
                loan_car.activated_at = datetime.datetime.utcnow()

                db.session.add(loan_sale)
                db.session.add(loan_notification)
                db.session.commit()
            except Exception as db_exc:
                db.session.rollback()
                print(f"Database error in approve_status: {str(db_exc)}")
                return jsonify({'success': False, 'error': 'Database error', 'message': str(db_exc)}), 500

            return jsonify({
                'success': True,
                'new_loan_car_status': loan_car.status,
                'notif_status': loan_notif.notification_type,
                'approved_at': loan_car.activated_at.isoformat() if loan_car.activated_at else None,
                'disbursement_id': disbursement_id
            })
            
    except Exception as e:
        print(f"Error in approve_status: {str(e)}")
        return jsonify({'success': False, 'error': 'Error in updating loan status', 'message': str(e)}), 500
    

@loan_api.route('/car-loan-status-reject', methods=['POST'])
def car_loan_status_reject():
    try:
        data = request.get_json()
        
        car_id = data.get('car_id')
        
        loan_car = LoanCar.query.filter_by(car_id=car_id).first()
        
        loan_car.status = 'available'
        loan_car.is_available = True
        
        LoanNotification.create_loan_status_notification(loan_car, 'rejected')
        
        
        return jsonify({'success': True, 'new_status': loan_car.status})
        
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'error': 'Error'})
        

@loan_api.route('/receive-monthly-commission', methods=['POST'])
def receive_monthly_commission():
    try:
        data = request.get_json()
        if not data or 'commission_amount' not in data or 'car_id' not in data:
            return jsonify({'success': False, 'error': 'Missing required data'}), 400
        
        car_id = data.get('car_id')
        disbursement_id = data.get('disbursement_id')
        is_paid = data.get('is_paid', False)
        monthly_commission_amount = data.get('commission_amount')
        
        car = Car.query.filter_by(id=car_id).first()
        if not car:
            return jsonify({'succes': False, 'error': 'Car not found'}), 404
        
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
        
        
        if not loan_sale.loan_term or loan_sale.loan_term <= 0:
            return jsonify({'success': False, 'error': 'Invalid loan term'}), 400
        
        loan_payment = LoanPayment.query.filter_by(loan_sale_id=loan_sale.id).first()
        
        monthly_payment = Decimal(loan_car.loan_sale_price) / loan_sale.loan_term
        
        if not loan_payment:
            loan_payment = LoanPayment(
                loan_sale_id=loan_sale.id,
                commission_received=Decimal(monthly_commission_amount),
                total_commission_received=0.0,
                date_commission_received = datetime.datetime.utcnow(),
                monthly_payment=Decimal(monthly_payment)
            )
            db.session.add(loan_payment)
        
        current_total = Decimal(loan_payment.total_commission_received or 0)
        new_total_received = Decimal(current_total) + Decimal(monthly_commission_amount)
        loan_sale_price = Decimal(loan_car.loan_sale_price)
        
        if new_total_received > loan_sale_price:
            return jsonify({
                'success': False,
                'error': f'Commission amount exceeds remaining balance. Expected: {Decimal(loan_car.loan_sale_price)}, Already received: {Decimal(loan_payment.total_commission_received or 0)}. Remaining Balance: {Decimal(loan_car.loan_sale_price) - Decimal(loan_payment.total_commission_received)}'
            }), 400
        
            
        loan_payment.commission_received = Decimal(monthly_commission_amount)
        loan_payment.total_commission_received = Decimal(new_total_received)
        loan_payment.date_commission_received = datetime.datetime.utcnow()
        
        if loan_payment.total_commission_received >= loan_car.loan_sale_price:
            loan_car.status = 'paid'
            car.is_available = False
            car.status = 'sold'
        
        db.session.commit()
        
        loan_notification = False
        if loan_car.status == 'paid':
            try:
                last_payment_notification = LoanNotification.last_payment_notification(loan_payment)
                if last_payment_notification:
                    db.session.add(last_payment_notification)
                    db.session.commit()
                    loan_notification = True
                else:
                    print("Warning: Failed to create last payment notification")
            except Exception as e:
                print(f"Error creating last payment notification: {e}")
        elif is_paid:
            try:
                loan_notification = LoanNotification.create_payment_notification(loan_payment)
                if loan_notification:
                    db.session.add(loan_notification)
                    db.session.commit()
                    loan_notification = True
                else:
                    print("Warning: Failed to create payment notification")
            except Exception as e:
                print(f"Error creating payment notification: {e}")
                
            
        return jsonify({
            'success': True,
            'disbursement_id': loan_sale.disbursement_id,
            'car_id': car_id,
            'commission_received': monthly_commission_amount,
            'total_commission_received': new_total_received,
            'total_loan_value': loan_car.loan_sale_price,
            'date_commission_received': loan_payment.date_commission_received.isoformat(),
            'loan_status': loan_car.status,
            'notification_created': loan_notification is not None,
            'message': 'Commission payment processed successfully'
        })
        
    except Exception as e:
        print(e)
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
        total_commission = loan_payment.total_commission_received

        return jsonify({
            'success': True,
            'disbursement_id': disbursement_id,
            'car_id': car_id,
            'total_commission': total_commission
        })
    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to fetch commission data', 'message': str(e)}), 500


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
