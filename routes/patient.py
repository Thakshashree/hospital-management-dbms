from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, Patient, Appointment, LabReport, Invoice, Feedback
from forms import AppointmentForm, FeedbackForm
from datetime import datetime, date
import re

patient_bp = Blueprint('patient', __name__, url_prefix='/patient')

def patient_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'patient':
            flash('Patient access only', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@patient_bp.before_request
@login_required
@patient_required
def before_request():
    pass

@patient_bp.route('/dashboard')
def dashboard():
    upcoming_appointments = Appointment.query.filter_by(patient_id=current_user.id, status='Approved').count()
    pending_bills = Invoice.query.filter_by(patient_id=current_user.id, status='Unpaid').count()
    latest_lab_report = LabReport.query.filter_by(patient_id=current_user.id).order_by(LabReport.created_at.desc()).first()
    
    next_appointments = Appointment.query.filter_by(patient_id=current_user.id).order_by(Appointment.date.asc()).limit(5).all()
    
    return render_template('patient_dashboard.html',
                           upcoming_appointments=upcoming_appointments,
                           pending_bills=pending_bills,
                           latest_lab_report=latest_lab_report,
                           next_appointments=next_appointments)

@patient_bp.route('/book', methods=['GET', 'POST'])
def book():
    form = AppointmentForm()
    doctors = User.query.filter_by(role='staff').all()
    form.doctor_id.choices = [(d.id, d.name) for d in doctors]
    
    if form.validate_on_submit():
        appt = Appointment(
            patient_id=current_user.id, doctor_id=form.doctor_id.data,
            date=form.date.data, time=form.time.data, reason=form.reason.data,
            status='Pending'
        )
        db.session.add(appt)
        db.session.commit()
        flash('Appointment booked successfully', 'success')
        return redirect(url_for('patient.appointments'))
        
    return render_template('book.html', form=form)

@patient_bp.route('/appointments')
def appointments():
    appointments = Appointment.query.filter_by(patient_id=current_user.id).all()
    return render_template('appointments.html', appointments=appointments)

@patient_bp.route('/lab')
def lab():
    reports = LabReport.query.filter_by(patient_id=current_user.id).all()
    total_reports = len(reports)
    completed_reports = sum(1 for r in reports if r.status == 'Completed')
    return render_template('patient_lab.html', 
                           reports=reports,
                           total_reports=total_reports,
                           completed_reports=completed_reports)

@patient_bp.route('/billing')
def billing():
    invoices = Invoice.query.filter_by(patient_id=current_user.id).all()
    total_unpaid = sum(1 for inv in invoices if inv.status == 'Unpaid')
    total_amount = sum(inv.amount for inv in invoices if inv.status == 'Unpaid')
    return render_template('patient_billing.html', 
                           invoices=invoices,
                           total_unpaid=total_unpaid,
                           total_amount=total_amount)

@patient_bp.route('/billing/pay/<int:invoice_id>', methods=['POST'])
def pay_bill(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    # Verify this invoice belongs to the current patient
    if invoice.patient_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('patient.billing'))
    
    invoice.status = 'Paid'
    db.session.commit()
    flash(f'Payment of ${invoice.amount:.2f} for INV-{invoice.id} was successful!', 'success')
    return redirect(url_for('patient.billing'))

@patient_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    patient_profile = Patient.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        # Update user name
        name = request.form.get('name', '').strip()
        if name:
            current_user.name = name
        
        # Update or create patient profile
        if not patient_profile:
            patient_profile = Patient(user_id=current_user.id)
            db.session.add(patient_profile)
        
        phone = request.form.get('phone', '').strip()
        if phone:
            patient_profile.phone = phone
            
        dob_str = request.form.get('dob', '').strip()
        if dob_str:
            try:
                patient_profile.dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        blood_group = request.form.get('blood_group', '').strip()
        patient_profile.blood_group = blood_group if blood_group else patient_profile.blood_group
        
        address = request.form.get('address', '').strip()
        if address:
            patient_profile.address = address
            
        emergency_contact = request.form.get('emergency_contact', '').strip()
        if emergency_contact:
            patient_profile.emergency_contact = emergency_contact
        
        # Handle password change
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        if new_password:
            if new_password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return render_template('patient_profile.html', patient_profile=patient_profile)
            if len(new_password) < 8:
                flash('Password must be at least 8 characters.', 'danger')
                return render_template('patient_profile.html', patient_profile=patient_profile)
            if not re.search(r'[A-Z]', new_password):
                flash('Password must contain at least one uppercase letter.', 'danger')
                return render_template('patient_profile.html', patient_profile=patient_profile)
            if not re.search(r'[!@#$%^&*(),.?":{}|<>_\\-]', new_password):
                flash('Password must contain at least one special character.', 'danger')
                return render_template('patient_profile.html', patient_profile=patient_profile)
            current_user.set_password(new_password)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('patient.profile'))
    
    return render_template('patient_profile.html', patient_profile=patient_profile)

@patient_bp.route('/feedback', methods=['GET', 'POST'])
def feedback():
    form = FeedbackForm()
    if form.validate_on_submit():
        feedback = Feedback(
            patient_id=current_user.id, rating=form.rating.data, comment=form.comment.data
        )
        db.session.add(feedback)
        db.session.commit()
        flash('Feedback submitted', 'success')
        return redirect(url_for('patient.dashboard'))
        
    return render_template('feedback.html', form=form)