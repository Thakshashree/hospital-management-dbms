from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from models import db, User, Patient, Doctor, Appointment
from forms import AppointmentForm
import datetime

public_bp = Blueprint('public', __name__)

@public_bp.route('/book', methods=['GET', 'POST'])
def public_book():
    form = AppointmentForm()
    
    # Populate doctors for the form
    doctors = Doctor.query.all()
    form.doctor_id.choices = [(d.user_id, f"Dr. {d.user.name} ({d.department or d.specialization})") for d in doctors if d.user]
    
    # Optional dynamic filtering could be handled via JS
    if request.method == 'GET' and current_user.is_authenticated and current_user.role == 'patient':
        # Auto-fill for logged in patients is handled in the template or by omitting the guest fields
        pass

    if form.validate_on_submit():
        patient_id = None
        if current_user.is_authenticated and current_user.role == 'patient':
            patient_id = current_user.id
        else:
            # Handle guest booking: create a provisional user and patient
            guest_name = request.form.get('guest_name')
            guest_email = request.form.get('guest_email')
            guest_phone = request.form.get('guest_phone')
            guest_age = request.form.get('guest_age')
            guest_gender = request.form.get('guest_gender')
            
            if not all([guest_name, guest_email, guest_phone]):
                flash('Please provide all guest details or log in.', 'danger')
                return render_template('public_book.html', form=form, doctors=doctors)
                
            # Check if user already exists
            existing_user = User.query.filter_by(email=guest_email).first()
            if existing_user:
                patient_id = existing_user.id
            else:
                new_user = User(
                    name=guest_name, 
                    email=guest_email, 
                    role='patient',
                    age=guest_age,
                    gender=guest_gender
                )
                # Set a dummy password for guest
                new_user.set_password('Guest123!')
                db.session.add(new_user)
                db.session.commit()
                
                new_patient = Patient(user_id=new_user.id, phone=guest_phone)
                db.session.add(new_patient)
                db.session.commit()
                patient_id = new_user.id

        appt = Appointment(
            patient_id=patient_id,
            doctor_id=form.doctor_id.data,
            department=form.department.data,
            hospital_branch=form.hospital_branch.data,
            appointment_type=form.appointment_type.data,
            date=form.date.data,
            time=form.time.data,
            reason=form.reason.data,
            symptoms=form.symptoms.data,
            status='Pending'
        )
        db.session.add(appt)
        db.session.commit()
        
        # Payment integration mock
        flash('Appointment booked successfully! Redirecting to payment...', 'success')
        # In a real app, redirect to a payment gateway. Here, we'll redirect to a success page.
        return redirect(url_for('public.booking_success', appt_id=appt.id))
        
    return render_template('public_book.html', form=form, doctors=doctors)

@public_bp.route('/booking_success/<int:appt_id>')
def booking_success(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    return render_template('booking_success.html', appt=appt)
