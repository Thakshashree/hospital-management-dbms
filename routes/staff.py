from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta, date
from models import db, User, Patient, Doctor, Appointment, Room, LabReport, Invoice, Inventory, Feedback
from forms import PatientForm, DoctorForm, RoomForm, LabReportForm, InvoiceForm, InventoryForm

staff_bp = Blueprint('staff', __name__, url_prefix='/staff')

def staff_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'staff':
            flash('Staff access only', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@staff_bp.before_request
@login_required
@staff_required
def before_request():
    pass

@staff_bp.route('/dashboard')
def dashboard():
    total_patients = User.query.filter_by(role='patient').count()
    today_appointments = Appointment.query.filter_by(date=date.today()).count()
    available_beds = Room.query.filter_by(status='Vacant').count()
    pending_bills = Invoice.query.filter_by(status='Unpaid').count()
    
    # Dummy chart data
    chart_labels = [(date.today() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    appt_counts = [5, 8, 12, 7, 10, 15, today_appointments]
    
    revenue_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    revenue_data = [5000, 7000, 6500, 8000, 9500, 11000]
    
    return render_template('staff.html', 
                           total_patients=total_patients, 
                           today_appointments=today_appointments, 
                           available_beds=available_beds, 
                           pending_bills=pending_bills,
                           chart_labels=chart_labels,
                           appt_counts=appt_counts,
                           revenue_labels=revenue_labels,
                           revenue_data=revenue_data)

@staff_bp.route('/patients', methods=['GET', 'POST'])
def patients():
    form = PatientForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, name=form.name.data, role='patient')
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        patient = Patient(
            user_id=user.id, dob=form.dob.data, phone=form.phone.data,
            address=form.address.data, blood_group=form.blood_group.data,
            emergency_contact=form.emergency_contact.data
        )
        db.session.add(patient)
        db.session.commit()
        flash('Patient added successfully', 'success')
        return redirect(url_for('staff.patients'))
        
    page = request.args.get('page', 1, type=int)
    patients = User.query.filter_by(role='patient').paginate(page=page, per_page=20)
    return render_template('patients.html', patients=patients, form=form)

@staff_bp.route('/doctors', methods=['GET', 'POST'])
def doctors():
    form = DoctorForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, name=form.name.data, role='staff', staff_role='Doctor')
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        doctor = Doctor(
            user_id=user.id, specialization=form.specialization.data,
            phone=form.phone.data, license_no=form.license_no.data, fee=form.fee.data
        )
        db.session.add(doctor)
        db.session.commit()
        flash('Doctor added successfully', 'success')
        return redirect(url_for('staff.doctors'))
        
    page = request.args.get('page', 1, type=int)
    doctors = User.query.filter_by(role='staff', staff_role='Doctor').paginate(page=page, per_page=20)
    return render_template('doctors.html', doctors=doctors, form=form)

from forms import AppointmentForm

@staff_bp.route('/appointments', methods=['GET', 'POST'])
def appointments():
    form = AppointmentForm()
    doctors = User.query.filter_by(role='staff').all() # or 'doctor' if you use that role
    form.doctor_id.choices = [(d.id, d.name) for d in doctors]
    patients = User.query.filter_by(role='patient').all()
    form.patient_id.choices = [(p.id, p.name) for p in patients]
    
    if form.validate_on_submit():
        appt = Appointment(
            patient_id=form.patient_id.data, doctor_id=form.doctor_id.data,
            date=form.date.data, time=form.time.data, reason=form.reason.data,
            status='Approved'
        )
        db.session.add(appt)
        db.session.commit()
        flash('Appointment created successfully', 'success')
        return redirect(url_for('staff.appointments'))
        
    query = Appointment.query
    if request.args.get('status'): query = query.filter_by(status=request.args.get('status'))
    if request.args.get('doctor_id'): query = query.filter_by(doctor_id=request.args.get('doctor_id'))
    if request.args.get('date'): 
        try:
            filter_date = datetime.strptime(request.args.get('date'), '%Y-%m-%d').date()
            query = query.filter_by(date=filter_date)
        except ValueError:
            pass
            
    appointments = query.all()
    return render_template('appointments.html', appointments=appointments, form=form)

@staff_bp.route('/rooms', methods=['GET', 'POST'])
def rooms():
    form = RoomForm()
    if form.validate_on_submit():
        room = Room(number=form.number.data, type=form.type.data)
        db.session.add(room)
        db.session.commit()
        flash('Room added successfully', 'success')
        return redirect(url_for('staff.rooms'))
    rooms = Room.query.all()
    return render_template('rooms.html', rooms=rooms, form=form)

import os
from werkzeug.utils import secure_filename

@staff_bp.route('/lab', methods=['GET', 'POST'])
def lab():
    form = LabReportForm()
    # Populate patient choices
    patients = User.query.filter_by(role='patient').all()
    form.patient_id.choices = [(p.id, p.name) for p in patients]
    
    if request.method == 'POST':
        # File upload handling would go here, omitting actual file saving for brevity
        # as standard form doesn't have file field currently
        report = LabReport(
            patient_id=form.patient_id.data, doctor_id=current_user.id,
            test_name=form.test_name.data, status='Completed'
        )
        db.session.add(report)
        db.session.commit()
        flash('Lab report created', 'success')
        return redirect(url_for('staff.lab'))
        
    reports = LabReport.query.all()
    return render_template('lab.html', reports=reports, form=form)

@staff_bp.route('/billing', methods=['GET', 'POST'])
def billing():
    form = InvoiceForm()
    patients = User.query.filter_by(role='patient').all()
    form.patient_id.choices = [(p.id, p.name) for p in patients]
    
    if form.validate_on_submit():
        invoice = Invoice(
            patient_id=form.patient_id.data, amount=form.amount.data,
            description=form.description.data, due_date=form.due_date.data
        )
        db.session.add(invoice)
        db.session.commit()
        flash('Invoice created', 'success')
        return redirect(url_for('staff.billing'))
        
    invoices = Invoice.query.all()
    return render_template('billing.html', invoices=invoices, form=form)

@staff_bp.route('/inventory', methods=['GET', 'POST'])
def inventory():
    form = InventoryForm()
    if form.validate_on_submit():
        item = Inventory(
            name=form.name.data, quantity=form.quantity.data, min_stock=form.min_stock.data
        )
        db.session.add(item)
        db.session.commit()
        flash('Item added', 'success')
        return redirect(url_for('staff.inventory'))
        
    items = Inventory.query.all()
    return render_template('inventory.html', items=items, form=form)

@staff_bp.route('/feedback')
def feedback():
    query = Feedback.query
    if request.args.get('status') == 'Resolved':
        query = query.filter_by(status='Resolved')
    feedbacks = query.all()
    return render_template('feedback.html', feedbacks=feedbacks)

@staff_bp.route('/records/<int:patient_id>')
def records(patient_id):
    patient_user = User.query.get_or_404(patient_id)
    appointments = Appointment.query.filter_by(patient_id=patient_id).all()
    lab_reports = LabReport.query.filter_by(patient_id=patient_id).all()
    invoices = Invoice.query.filter_by(patient_id=patient_id).all()
    
    return render_template('records.html', 
                           patient=patient_user,
                           appointments=appointments,
                           lab_reports=lab_reports,
                           invoices=invoices)