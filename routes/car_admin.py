from flask import Flask, flash, render_template, redirect, url_for, jsonify, make_response, Blueprint, session, current_app, request
from datetime import datetime
from flask_login import login_required, current_user, logout_user
from models.loan_car import LoanCar
from models.car import Car
from models import db
from functools import wraps

car_admin = Blueprint('car_admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('admin.admin_login'))
        
        if 'last_activity' in session:
            last_activity = datetime.fromtimestamp(session['last_activity'])
            if (datetime.now() - last_activity).total_seconds() > 1800:  
             
                current_app.logger.warning(f"Admin session timeout for user {current_user.id}")
                
                session.clear()
                logout_user()
                
                flash('Your session has expired. Please log in again.', 'warning')
                return redirect(url_for('admin.admin_login'))
            
            session['last_activity'] = datetime.now().timestamp()
            session.modified = True
        
        return f(*args, **kwargs)
    return decorated_function


@car_admin.route('/loan-cars')
@login_required
@admin_required
def manage_loan_cars():

    available_cars = Car.query.filter_by(is_available=True).all()

    loan_cars = db.session.query(LoanCar, Car).join(Car).filter(
        LoanCar.status.in_(['pending', 'active', 'available'])
    ).all()

    return render_template('admin/loan_cars.html',  
                         available_cars=available_cars, 
                         loan_cars=loan_cars)

@car_admin.route('/offer-car-for-loan', methods=['POST'])
@login_required
@admin_required
def offer_car_for_loan():
    try:
        car_id = request.form.get('car_id')
        loan_sale_price = float(request.form.get('loan_sale_price'))
        commission_rate = float(request.form.get('commission_rate', 30.0))

        car = Car.query.get(car_id)
        if not car or not car.is_available:
            flash('Car not found or not available', 'error')
            return redirect(url_for('car_admin.manage_loan_cars'))
        
        existing_loan_car = LoanCar.query.filter_by(car_id=car_id).first()
        
        if existing_loan_car:
            if existing_loan_car.status in ['pending', 'active']:
                flash('Car is already offered for loan', 'error')
                return redirect(url_for('car_admin.manage_loan_cars'))
            
            elif existing_loan_car.status in ['withdrawn']:
                existing_loan_car.status = 'available'
                existing_loan_car.loan_sale_price = loan_sale_price
                existing_loan_car.commission_rate = commission_rate
                existing_loan_car.date_offered = datetime.utcnow()
                existing_loan_car.date_withdrawn = None
                existing_loan_car.offered_by = current_user.id
                loan_car_to_commit = existing_loan_car
        
        else:

            loan_car_to_commit = LoanCar(
                car_id=car_id,
                loan_sale_price=loan_sale_price,
                commission_rate=commission_rate,
                offered_by=current_user.id,
                status='available',
                date_offered=datetime.utcnow()
            )
            db.session.add(loan_car_to_commit)

        db.session.commit()
        flash(f'Car {car.make} {car.model} successfully offered for loan', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error offering car for loan: {str(e)}', 'error')
        
    return redirect(url_for('car_admin.manage_loan_cars'))


@car_admin.route('/update-loan-car/<int:loan_car_id>', methods=['POST'])
@login_required
@admin_required
def update_loan_car(loan_car_id):
    """API endpoint for modal updates"""
    try:
        loan_car = LoanCar.query.get_or_404(loan_car_id)

        if not loan_car:
            return jsonify({
                'success': False, 
                'message': 'Loan car not found'
            }), 404
        
        if loan_car.status not in ['pending', 'active']:
            return jsonify({
                'success': False, 
                'message': f'Cannot update loan car with status: {loan_car.status}'
            }), 400
        
        loan_car.loan_sale_price = float(request.form['loan_sale_price'])
        loan_car.commission_rate = float(request.form['commission_rate'])

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False, 
                'message': 'Failed to update loan car'
            }), 500
            
        return jsonify({
            'success': True, 
            'message': 'Loan car updated successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'error': 'Unexpected Error',
            'message': str(e)
        }), 500

@car_admin.route('/withdraw-loan-car/<int:loan_car_id>', methods=['POST'])
@login_required
@admin_required
def withdraw_loan_car(loan_car_id):
    """Withdraw a loan car offering"""
    try:
        loan_car = LoanCar.query.get(loan_car_id)
        
        if not loan_car:
            flash('Loan car not found', 'error')
            return redirect(url_for('car_admin.manage_loan_cars'))
        
        if loan_car.status != 'available':
            flash(f'Cannot withdraw loan car. Current status: {loan_car.status}', 'error')
            return redirect(url_for('car_admin.manage_loan_cars'))
        
        loan_car.status = 'withdrawn'
        loan_car.date_withdrawn = datetime.utcnow()

        try:
            db.session.commit()
            flash('Loan car withdrawn successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Failed to withdraw loan car', 'error')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error withdrawing loan car: {str(e)}', 'error')

    return redirect(url_for('car_admin.manage_loan_cars'))

@car_admin.route('/loan-sale-details/<int:sale_id>')
@login_required
@admin_required
def loan_sale_details(sale_id):
    """View loan sale details"""
    loan_car = LoanCar.query.get_or_404(sale_id)
    car = Car.query.get_or_404(loan_car.car_id)
    
    return render_template('admin/loan_details.html', 
                         loan_car=loan_car, 
                         car=car)