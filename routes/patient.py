from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, Appointment, LabReport, Invoice, Feedback
from forms import AppointmentForm, FeedbackForm
from datetime import datetime

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
    doctors = User.query.filter_by(role='staff').all() # Assuming staff can act as doctors or role='doctor' is used
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
    return render_template('lab.html', reports=reports)

@patient_bp.route('/billing')
def billing():
    invoices = Invoice.query.filter_by(patient_id=current_user.id).all()
    return render_template('billing.html', invoices=invoices)

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