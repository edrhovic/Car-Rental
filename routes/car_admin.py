from flask import Flask, flash, render_template, redirect, url_for, jsonify, make_response, Blueprint, session, current_app, request
from datetime import datetime, timedelta
from flask_login import login_required, current_user, logout_user
from models.loan_car import LoanCar, LoanSale, LoanPayment
from models.car import Car
from models import db
from functools import wraps
import json
from sqlalchemy import func, extract
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

@car_admin.route('/loan-cars-dashboard')
@login_required
@admin_required
def loan_cars_dashboard():
    """Dashboard for loan cars"""
    
    
    current_date = datetime.now()
    current_year = current_date.year
    
    total_active_loans = LoanCar.query.filter_by(status='active').count()
    total_loan_value = db.session.query(func.sum(LoanCar.loan_sale_price)).filter_by(status='active').scalar() or 0.00
    total_commissions = db.session.query(func.sum(LoanPayment.commission_received)).scalar() or 0.00
    
    pending_commissions = db.session.query(
        func.sum(LoanPayment.total_commission_expected - LoanPayment.commission_received)
    ).filter(
        LoanPayment.commission_received < LoanPayment.total_commission_expected
    ).scalar() or 0.00
    
    
    monthly_data = []
    monthly_labels = []
    monthly_commissions = []
    monthly_active_loans = []
    
    for i in range(11, -1, -1):
        # Calculate the date for each month
        target_date = current_date - timedelta(days=30*i)
        month_year = target_date.strftime('%Y-%m')
        month_name_short = target_date.strftime('%b %Y')
        
        # Get commission data for the month
        commission_data = db.session.query(
            func.sum(LoanPayment.commission_received)
        ).filter(
            extract('year', LoanPayment.date_commission_received) == target_date.year,
            extract('month', LoanPayment.date_commission_received) == target_date.month
        ).scalar() or 0
        
        # Get active loans for the month (loans that were active during that month)
        active_loans_count = db.session.query(
            func.count(LoanCar.id)
        ).filter(
            LoanCar.status == 'active',
            LoanCar.activated_at <= target_date.replace(day=1) + timedelta(days=32)
        ).scalar() or 0
        
        monthly_labels.append(month_name_short)
        monthly_commissions.append(float(commission_data))
        monthly_active_loans.append(active_loans_count)
    
    # Get recent loan activities (recently accepted loans)
    recent_activities = db.session.query(LoanSale).join(
        LoanCar, LoanSale.loan_car_id == LoanCar.id
    ).filter(
        LoanCar.status == 'active'
    ).order_by(
        LoanCar.activated_at.desc()
    ).limit(10).all()
    
    # Get all loan cars for the table
    loan_cars = db.session.query(LoanCar).join(
        Car, LoanCar.car_id == Car.id
    ).filter(
        LoanCar.status.in_(['active', 'pending', 'approved'])
    ).order_by(
        LoanCar.date_offered.desc()
    ).all()
    
    statistics = {
        'total_active_loan_cars': total_active_loans,
        'total_loan_value': total_loan_value,
        'total_commissions': total_commissions,
        'pending_commissions': pending_commissions
    }

    return render_template('admin/loan_dashboard.html', statistics=statistics,
                         monthly_labels=json.dumps(monthly_labels),
                         monthly_commissions=json.dumps(monthly_commissions),
                         monthly_active_loans=json.dumps(monthly_active_loans),
                         recent_activities=recent_activities,
                         loan_cars=loan_cars)


@car_admin.route('/loan-cars')
@login_required
@admin_required
def manage_loan_cars():

    available_cars = Car.query.filter_by(is_available=True, status= 'available').all()

    loan_cars = db.session.query(LoanCar, Car).join(Car).filter(
        LoanCar.status.in_(['pending', 'active', 'available', 'approved'])
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
        commission_rate = float(request.form.get('commission_rate', 10.0))

        car = Car.query.get(car_id)
        if not car or not car.is_available or car.status != 'available':
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
                car.status = 'offered_for_loan'
                car.is_available = False
        
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
            car.status = 'offered_for_loan'
            car.is_available = False

        db.session.commit()
        flash(f'Car {car.make} {car.model} successfully offered for loan', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error offering car for loan: {str(e)}', 'error')
        
    return redirect(url_for('car_admin.manage_loan_cars'))

@car_admin.route('/bulk-offer-cars-for-loan', methods=['POST'])
@login_required
@admin_required
def bulk_offer_cars_for_loan():
    try:
        # Get form data
        car_ids_str = request.form.get('bulk_car_ids', '')
        loan_sale_price = float(request.form.get('bulk_loan_sale_price'))
        commission_rate = float(request.form.get('commission_rate', 10.0))
        
        # Parse car IDs
        if not car_ids_str:
            flash('No cars selected for bulk offer', 'error')
            return redirect(url_for('car_admin.manage_loan_cars'))
        
        car_ids = [int(id.strip()) for id in car_ids_str.split(',') if id.strip()]
        
        if not car_ids:
            flash('No valid car IDs provided', 'error')
            return redirect(url_for('car_admin.manage_loan_cars'))
        
        # Track results
        success_count = 0
        error_count = 0
        errors = []
        
        # Process each car
        for car_id in car_ids:
            try:
                # Get car and validate
                car = Car.query.get(car_id)
                if not car:
                    errors.append(f"Car ID {car_id} not found")
                    error_count += 1
                    continue
                
                if not car.is_available or car.status != 'available':
                    errors.append(f"{car.make} {car.model} is not available")
                    error_count += 1
                    continue
                
                # Check if already offered
                existing_loan_car = LoanCar.query.filter_by(car_id=car_id).first()
                
                if existing_loan_car:
                    if existing_loan_car.status in ['pending', 'active']:
                        errors.append(f"{car.make} {car.model} is already offered for loan")
                        error_count += 1
                        continue
                    
                    elif existing_loan_car.status in ['withdrawn']:
                        # Re-offer withdrawn car
                        existing_loan_car.status = 'available'
                        existing_loan_car.loan_sale_price = loan_sale_price
                        existing_loan_car.commission_rate = commission_rate
                        existing_loan_car.date_offered = datetime.utcnow()
                        existing_loan_car.date_withdrawn = None
                        existing_loan_car.offered_by = current_user.id
                        car.status = 'offered_for_loan'
                        car.is_available = False
                        success_count += 1
                else:
                    # Create new loan car entry
                    loan_car = LoanCar(
                        car_id=car_id,
                        loan_sale_price=loan_sale_price,
                        commission_rate=commission_rate,
                        offered_by=current_user.id,
                        status='available',
                        date_offered=datetime.utcnow()
                    )
                    db.session.add(loan_car)
                    car.status = 'offered_for_loan'
                    car.is_available = False
                    success_count += 1
                    
            except ValueError as ve:
                errors.append(f"Invalid data for car ID {car_id}: {str(ve)}")
                error_count += 1
            except Exception as e:
                errors.append(f"Error processing car ID {car_id}: {str(e)}")
                error_count += 1
        
        # Commit all changes if there were any successes
        if success_count > 0:
            db.session.commit()
        
        # Generate appropriate flash messages
        if success_count > 0 and error_count == 0:
            flash(f'Successfully offered {success_count} car{"s" if success_count > 1 else ""} for loan', 'success')
        elif success_count > 0 and error_count > 0:
            flash(f'Successfully offered {success_count} car{"s" if success_count > 1 else ""} for loan. {error_count} car{"s" if error_count > 1 else ""} had errors.', 'warning')
            for error in errors[:3]:  # Show first 3 errors
                flash(error, 'error')
            if len(errors) > 3:
                flash(f'... and {len(errors) - 3} more errors', 'error')
        else:
            flash(f'Failed to offer any cars for loan. {error_count} error{"s" if error_count > 1 else ""} occurred.', 'error')
            for error in errors[:5]:  # Show first 5 errors
                flash(error, 'error')
        
    except ValueError as ve:
        db.session.rollback()
        flash(f'Invalid loan sale price: {str(ve)}', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing bulk offer: {str(e)}', 'error')
    
    return redirect(url_for('car_admin.manage_loan_cars'))



@car_admin.route('/offer-all-cars-for-loan')
@login_required
@admin_required
def offer_all_cars_for_loan():
    """Route to redirect to bulk offer with all available cars pre-selected"""
    try:
        # Get all available cars that are not already offered for loan
        offered_car_ids = db.session.query(LoanCar.car_id).filter(
            LoanCar.status.in_(['available', 'pending', 'active'])
        ).subquery()
        
        available_cars = Car.query.filter(
            Car.is_available == True,
            Car.status == 'available',
            ~Car.id.in_(offered_car_ids)
        ).all()
        
        if not available_cars:
            flash('No available cars to offer for loan', 'info')
            return redirect(url_for('car_admin.manage_loan_cars'))
        
        # Create a list of car IDs
        car_ids = [str(car.id) for car in available_cars]
        
        # Flash message about pre-selection
        flash(f'{len(available_cars)} available cars have been pre-selected for bulk offer', 'info')
        
        # Redirect to manage page with a parameter to indicate pre-selection
        return redirect(url_for('car_admin.manage_loan_cars', preselect_all='true'))
        
    except Exception as e:
        flash(f'Error loading available cars: {str(e)}', 'error')
        return redirect(url_for('car_admin.manage_loan_cars'))


@car_admin.route('/car-loan-management')
@login_required
@admin_required
def car_loan_management():
    """View all active loan cars"""
    
    statistics = {
        'total_loan_cars': LoanCar.query.count(),
        'active_loan_cars': LoanCar.query.filter_by(status='active').all(),
        'total_available_cars': LoanCar.query.filter_by(status='available').count(),
        'total_commissions': db.session.query(db.func.sum(LoanPayment.commission_received)).scalar() or 0.00,
        'total_active_loan_cars': LoanCar.query.filter_by(status='active').count(),
        'total_pending_loan_cars': LoanCar.query.filter_by(status='pending').count(),
        'total_available_loan_cars': LoanCar.query.filter_by(status='available').count
    }
    
    return render_template('admin/car_loan_management.html', statistics=statistics)



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
        
        car = Car.query.get(loan_car.car_id)
        
        if loan_car.status != 'available':
            flash(f'Cannot withdraw loan car. Current status: {loan_car.status}', 'error')
            return redirect(url_for('car_admin.manage_loan_cars'))
        
        loan_car.status = 'withdrawn'
        loan_car.date_withdrawn = datetime.utcnow()
        car.status = 'available'
        car.is_available = True

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
    loan_sale = LoanSale.query.filter_by(loan_car_id=loan_car.id).first()

    
    car = Car.query.get_or_404(loan_car.car_id)
    
    return render_template('admin/loan_details.html', 
                         loan_car=loan_car, 
                         car=car, loan_sale=loan_sale)
    
