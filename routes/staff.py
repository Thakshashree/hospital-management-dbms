import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta, date
from werkzeug.utils import secure_filename
from models import db, User, Patient, Doctor, Appointment, Room, LabReport, Invoice, Inventory, Feedback
from forms import PatientForm, DoctorForm, RoomForm, LabReportForm, InvoiceForm, InventoryForm, AppointmentForm

staff_bp = Blueprint('staff', __name__, url_prefix='/staff')

# ─────────────────────────────── AUTH GUARD ───────────────────────────────
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

# ─────────────────────────────── UPLOAD HELPER ────────────────────────────
def get_upload_folder():
    upload_dir = os.path.join(current_app.root_path, '..', 'static', 'uploads', 'lab_reports')
    os.makedirs(upload_dir, exist_ok=True)
    return os.path.abspath(upload_dir)

# ═══════════════════════════════════════════════════════════════════════════
# 9. DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════
@staff_bp.route('/dashboard')
def dashboard():
    total_patients    = User.query.filter_by(role='patient').count()
    today_appointments = Appointment.query.filter_by(date=date.today()).count()
    available_beds    = Room.query.filter_by(status='Vacant').count()
    pending_bills     = Invoice.query.filter_by(status='Unpaid').count()

    chart_labels  = [(date.today() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    appt_counts   = [5, 8, 12, 7, 10, 15, today_appointments]
    revenue_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    revenue_data   = [5000, 7000, 6500, 8000, 9500, 11000]

    return render_template('staff.html',
                           total_patients=total_patients,
                           today_appointments=today_appointments,
                           available_beds=available_beds,
                           pending_bills=pending_bills,
                           chart_labels=chart_labels,
                           appt_counts=appt_counts,
                           revenue_labels=revenue_labels,
                           revenue_data=revenue_data)

# ═══════════════════════════════════════════════════════════════════════════
# 1. PATIENTS
# ═══════════════════════════════════════════════════════════════════════════
@staff_bp.route('/patients', methods=['GET', 'POST'])
def patients():
    form = PatientForm()
    if form.validate_on_submit():
        try:
            user = User(
                email=form.email.data,   # CHANGE COLUMN NAME HERE if your DB differs
                name=form.name.data,     # CHANGE COLUMN NAME HERE
                role='patient'
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()           # get user.id before commit

            patient = Patient(
                user_id=user.id,
                dob=form.dob.data,
                phone=form.phone.data,           # CHANGE COLUMN NAME HERE
                address=form.address.data,       # CHANGE COLUMN NAME HERE
                blood_group=form.blood_group.data,
                emergency_contact=form.emergency_contact.data
            )
            db.session.add(patient)
            db.session.commit()
            flash('Patient registered successfully!', 'success')
            return redirect(url_for('staff.patients'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving patient: {str(e)}', 'danger')
    elif request.method == 'POST':
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", "danger")

    page = request.args.get('page', 1, type=int)
    patients_list = User.query.filter_by(role='patient').paginate(page=page, per_page=20)
    return render_template('patients.html', patients=patients_list, form=form)


@staff_bp.route('/delete_patient/<int:id>', methods=['POST'])
def delete_patient(id):
    try:
        user = User.query.get_or_404(id)
        if user.role != 'patient':
            flash('User is not a patient.', 'warning')
            return redirect(url_for('staff.patients'))
        # delete linked patient profile first
        for p in user.patient_profile:
            db.session.delete(p)
        db.session.delete(user)
        db.session.commit()
        flash('Patient deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting patient: {str(e)}', 'danger')
    return redirect(url_for('staff.patients'))

# ═══════════════════════════════════════════════════════════════════════════
# 2. DOCTORS
# ═══════════════════════════════════════════════════════════════════════════
@staff_bp.route('/doctors', methods=['GET', 'POST'])
def doctors():
    form = DoctorForm()
    if form.validate_on_submit():
        try:
            user = User(
                email=form.email.data,
                name=form.name.data,
                role='staff',
                staff_role='Doctor',
                department=form.department.data
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()

            doctor = Doctor(
                user_id=user.id,
                specialization=form.specialization.data,  # CHANGE COLUMN NAME HERE
                department=form.department.data,
                working_hours=form.working_hours.data,
                phone=form.phone.data,                    # CHANGE COLUMN NAME HERE
                license_no=form.license_no.data,
                fee=form.fee.data
            )
            db.session.add(doctor)
            db.session.commit()
            flash('Doctor registered successfully!', 'success')
            return redirect(url_for('staff.doctors'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving doctor: {str(e)}', 'danger')
    elif request.method == 'POST':
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", "danger")

    page = request.args.get('page', 1, type=int)
    doctors_list = User.query.filter_by(role='staff', staff_role='Doctor').paginate(page=page, per_page=20)
    return render_template('doctors.html', doctors=doctors_list, form=form)


@staff_bp.route('/delete_doctor/<int:id>', methods=['POST'])
def delete_doctor(id):
    try:
        user = User.query.get_or_404(id)
        for d in user.doctor_profile:
            db.session.delete(d)
        db.session.delete(user)
        db.session.commit()
        flash('Doctor deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting doctor: {str(e)}', 'danger')
    return redirect(url_for('staff.doctors'))

# ═══════════════════════════════════════════════════════════════════════════
# 3. APPOINTMENTS
# ═══════════════════════════════════════════════════════════════════════════
@staff_bp.route('/appointments', methods=['GET', 'POST'])
def appointments():
    form = AppointmentForm()
    doctors_qs  = User.query.filter_by(role='staff').all()
    patients_qs = User.query.filter_by(role='patient').all()
    form.doctor_id.choices  = [(d.id, d.name) for d in doctors_qs]
    form.patient_id.choices = [(p.id, p.name) for p in patients_qs]

    if form.validate_on_submit():
        try:
            appt = Appointment(
                patient_id=form.patient_id.data,       # CHANGE COLUMN NAME HERE
                doctor_id=form.doctor_id.data,         # CHANGE COLUMN NAME HERE
                department=form.department.data,
                hospital_branch=form.hospital_branch.data,
                appointment_type=form.appointment_type.data,
                date=form.date.data,                   # CHANGE COLUMN NAME HERE
                time=form.time.data,                   # CHANGE COLUMN NAME HERE
                reason=form.reason.data,
                symptoms=form.symptoms.data,
                status='Approved'
            )
            db.session.add(appt)
            db.session.commit()
            flash('Appointment created successfully!', 'success')
            return redirect(url_for('staff.appointments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating appointment: {str(e)}', 'danger')
    elif request.method == 'POST':
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", "danger")

    query = Appointment.query
    if request.args.get('status'):
        query = query.filter_by(status=request.args.get('status'))
    if request.args.get('doctor_id'):
        query = query.filter_by(doctor_id=request.args.get('doctor_id'))
    if request.args.get('date'):
        try:
            filter_date = datetime.strptime(request.args.get('date'), '%Y-%m-%d').date()
            query = query.filter_by(date=filter_date)
        except ValueError:
            pass

    appointments_list = query.all()
    return render_template('appointments.html', appointments=appointments_list, form=form)


@staff_bp.route('/edit_appointment/<int:id>', methods=['GET', 'POST'])
def edit_appointment(id):
    appt = Appointment.query.get_or_404(id)
    form = AppointmentForm(obj=appt)
    doctors_qs  = User.query.filter_by(role='staff').all()
    patients_qs = User.query.filter_by(role='patient').all()
    form.doctor_id.choices  = [(d.id, d.name) for d in doctors_qs]
    form.patient_id.choices = [(p.id, p.name) for p in patients_qs]

    if form.validate_on_submit():
        try:
            appt.patient_id      = form.patient_id.data
            appt.doctor_id       = form.doctor_id.data
            appt.department      = form.department.data
            appt.hospital_branch = form.hospital_branch.data
            appt.appointment_type = form.appointment_type.data
            appt.date            = form.date.data
            appt.time            = form.time.data
            appt.reason          = form.reason.data
            appt.symptoms        = form.symptoms.data
            db.session.commit()
            flash('Appointment updated successfully!', 'success')
            return redirect(url_for('staff.appointments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating appointment: {str(e)}', 'danger')
    elif request.method == 'POST':
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", "danger")

    return render_template('edit_appointment.html', form=form, appt=appt)


@staff_bp.route('/delete_appointment/<int:id>', methods=['POST'])
def delete_appointment(id):
    try:
        appt = Appointment.query.get_or_404(id)
        db.session.delete(appt)
        db.session.commit()
        flash('Appointment deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting appointment: {str(e)}', 'danger')
    return redirect(url_for('staff.appointments'))


@staff_bp.route('/approve_appointment/<int:id>', methods=['POST'])
def approve_appointment(id):
    try:
        appt = Appointment.query.get_or_404(id)
        appt.status = 'Approved'
        db.session.commit()
        flash('Appointment approved.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('staff.appointments'))


@staff_bp.route('/cancel_appointment/<int:id>', methods=['POST'])
def cancel_appointment(id):
    try:
        appt = Appointment.query.get_or_404(id)
        appt.status = 'Cancelled'
        db.session.commit()
        flash('Appointment cancelled.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('staff.appointments'))

# ═══════════════════════════════════════════════════════════════════════════
# 4. ROOMS
# ═══════════════════════════════════════════════════════════════════════════
@staff_bp.route('/rooms', methods=['GET', 'POST'])
def rooms():
    form = RoomForm()
    if form.validate_on_submit():
        try:
            room = Room(
                number=form.number.data,  # CHANGE COLUMN NAME HERE if your DB uses room_number
                type=form.type.data       # CHANGE COLUMN NAME HERE
            )
            db.session.add(room)
            db.session.commit()
            flash('Room added successfully!', 'success')
            return redirect(url_for('staff.rooms'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding room: {str(e)}', 'danger')
    elif request.method == 'POST':
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", "danger")

    rooms_list = Room.query.all()
    return render_template('rooms.html', rooms=rooms_list, form=form)


@staff_bp.route('/toggle_room/<int:id>', methods=['POST'])
def toggle_room(id):
    """Toggle room status between Vacant and Occupied."""
    try:
        room = Room.query.get_or_404(id)
        # CHANGE STATUS VALUES HERE if your DB uses 'Available'/'Occupied' instead
        if room.status == 'Vacant':
            room.status = 'Occupied'
            flash(f'Room {room.number} marked as Occupied.', 'warning')
        else:
            room.status = 'Vacant'
            room.patient_id = None
            flash(f'Room {room.number} marked as Vacant.', 'success')
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating room: {str(e)}', 'danger')
    return redirect(url_for('staff.rooms'))


@staff_bp.route('/delete_room/<int:id>', methods=['POST'])
def delete_room(id):
    try:
        room = Room.query.get_or_404(id)
        db.session.delete(room)
        db.session.commit()
        flash('Room deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting room: {str(e)}', 'danger')
    return redirect(url_for('staff.rooms'))

# ═══════════════════════════════════════════════════════════════════════════
# 5. LAB REPORTS
# ═══════════════════════════════════════════════════════════════════════════
@staff_bp.route('/lab', methods=['GET', 'POST'])
def lab():
    form = LabReportForm()
    patients_qs = User.query.filter_by(role='patient').all()
    form.patient_id.choices = [(p.id, p.name) for p in patients_qs]

    if request.method == 'POST':
        if form.validate():
            try:
                filename = None
                if 'file' in request.files:
                    file = request.files['file']
                    if file and file.filename:
                        filename = secure_filename(file.filename)
                        upload_dir = get_upload_folder()
                        file.save(os.path.join(upload_dir, filename))

                report = LabReport(
                    patient_id=form.patient_id.data,   # CHANGE COLUMN NAME HERE
                    doctor_id=current_user.id,
                    test_name=form.test_name.data,     # CHANGE COLUMN NAME HERE
                    file_path=filename,                # CHANGE COLUMN NAME HERE (some DBs use 'filename')
                    status='Completed'
                )
                db.session.add(report)
                db.session.commit()
                flash('Lab report saved successfully!', 'success')
                return redirect(url_for('staff.lab'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error saving lab report: {str(e)}', 'danger')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{getattr(form, field).label.text}: {error}", "danger")

    reports = LabReport.query.order_by(LabReport.created_at.desc()).all()
    return render_template('lab.html', reports=reports, form=form)


@staff_bp.route('/delete_lab/<int:id>', methods=['POST'])
def delete_lab(id):
    try:
        report = LabReport.query.get_or_404(id)
        db.session.delete(report)
        db.session.commit()
        flash('Lab report deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('staff.lab'))

# ═══════════════════════════════════════════════════════════════════════════
# 6. INVENTORY
# ═══════════════════════════════════════════════════════════════════════════
@staff_bp.route('/inventory', methods=['GET', 'POST'])
def inventory():
    form = InventoryForm()
    if form.validate_on_submit():
        try:
            item = Inventory(
                name=form.name.data,         # CHANGE COLUMN NAME HERE (some DBs use 'item_name')
                quantity=form.quantity.data,  # CHANGE COLUMN NAME HERE
                min_stock=form.min_stock.data
            )
            db.session.add(item)
            db.session.commit()
            flash('Inventory item added!', 'success')
            return redirect(url_for('staff.inventory'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding item: {str(e)}', 'danger')
    elif request.method == 'POST':
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", "danger")

    items = Inventory.query.all()
    return render_template('inventory.html', items=items, form=form)


@staff_bp.route('/edit_inventory/<int:id>', methods=['GET', 'POST'])
def edit_inventory(id):
    item = Inventory.query.get_or_404(id)
    form = InventoryForm(obj=item)
    if form.validate_on_submit():
        try:
            item.name      = form.name.data        # CHANGE COLUMN NAME HERE
            item.quantity  = form.quantity.data    # CHANGE COLUMN NAME HERE
            item.min_stock = form.min_stock.data
            db.session.commit()
            flash('Item updated successfully!', 'success')
            return redirect(url_for('staff.inventory'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating item: {str(e)}', 'danger')
    elif request.method == 'POST':
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", "danger")
    return render_template('edit_inventory.html', form=form, item=item)


@staff_bp.route('/delete_inventory/<int:id>', methods=['POST'])
def delete_inventory(id):
    try:
        item = Inventory.query.get_or_404(id)
        db.session.delete(item)
        db.session.commit()
        flash('Item deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('staff.inventory'))

# ═══════════════════════════════════════════════════════════════════════════
# 7. FEEDBACK
# ═══════════════════════════════════════════════════════════════════════════
@staff_bp.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        try:
            # Staff can log anonymous/manual feedback
            name    = request.form.get('name', 'Anonymous')   # CHANGE COLUMN NAME HERE
            comment = request.form.get('comment', '')          # CHANGE COLUMN NAME HERE (some DBs use 'message')
            rating  = int(request.form.get('rating', 3))       # CHANGE COLUMN NAME HERE

            fb = Feedback(
                patient_id=None,   # NULL for anonymous entries
                rating=rating,
                comment=comment,
                status='Open'
            )
            db.session.add(fb)
            db.session.commit()
            flash('Feedback submitted successfully!', 'success')
            return redirect(url_for('staff.feedback'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving feedback: {str(e)}', 'danger')

    query = Feedback.query
    if request.args.get('status') == 'Resolved':
        query = query.filter_by(status='Resolved')
    feedbacks = query.order_by(Feedback.created_at.desc()).all()
    return render_template('feedback.html', feedbacks=feedbacks)


@staff_bp.route('/resolve_feedback/<int:id>', methods=['POST'])
def resolve_feedback(id):
    try:
        fb = Feedback.query.get_or_404(id)
        fb.status = 'Resolved'
        db.session.commit()
        flash('Feedback marked as resolved.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('staff.feedback'))


@staff_bp.route('/delete_feedback/<int:id>', methods=['POST'])
def delete_feedback(id):
    try:
        fb = Feedback.query.get_or_404(id)
        db.session.delete(fb)
        db.session.commit()
        flash('Feedback deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('staff.feedback'))

# ═══════════════════════════════════════════════════════════════════════════
# 8. RECORDS  – Dashboard stats (not patient-specific)
# ═══════════════════════════════════════════════════════════════════════════
@staff_bp.route('/records')
def records():
    total_patients    = User.query.filter_by(role='patient').count()
    total_doctors     = User.query.filter_by(role='staff', staff_role='Doctor').count()
    total_appointments = Appointment.query.count()
    available_rooms   = Room.query.filter_by(status='Vacant').count()   # CHANGE STATUS VALUE HERE
    total_rooms       = Room.query.count()
    pending_bills     = Invoice.query.filter_by(status='Unpaid').count()
    total_lab         = LabReport.query.count()
    total_inventory   = Inventory.query.count()
    total_feedback    = Feedback.query.count()

    recent_appointments = Appointment.query.order_by(Appointment.created_at.desc()).limit(10).all()
    recent_patients     = User.query.filter_by(role='patient').order_by(User.created_at.desc()).limit(5).all()

    return render_template('records.html',
                           total_patients=total_patients,
                           total_doctors=total_doctors,
                           total_appointments=total_appointments,
                           available_rooms=available_rooms,
                           total_rooms=total_rooms,
                           pending_bills=pending_bills,
                           total_lab=total_lab,
                           total_inventory=total_inventory,
                           total_feedback=total_feedback,
                           recent_appointments=recent_appointments,
                           recent_patients=recent_patients)


# Patient-specific records (keep for backward compat with sidebar link)
@staff_bp.route('/records/patient/<int:patient_id>')
def patient_records(patient_id):
    patient_user = User.query.get_or_404(patient_id)
    appointments  = Appointment.query.filter_by(patient_id=patient_id).all()
    lab_reports   = LabReport.query.filter_by(patient_id=patient_id).all()
    invoices      = Invoice.query.filter_by(patient_id=patient_id).all()
    return render_template('patient_records.html',
                           patient=patient_user,
                           appointments=appointments,
                           lab_reports=lab_reports,
                           invoices=invoices)

# ═══════════════════════════════════════════════════════════════════════════
# BILLING (unchanged but with try/except added)
# ═══════════════════════════════════════════════════════════════════════════
@staff_bp.route('/billing', methods=['GET', 'POST'])
def billing():
    form = InvoiceForm()
    patients_qs = User.query.filter_by(role='patient').all()
    form.patient_id.choices = [(p.id, p.name) for p in patients_qs]

    if form.validate_on_submit():
        try:
            invoice = Invoice(
                patient_id=form.patient_id.data,
                amount=form.amount.data,
                description=form.description.data,
                due_date=form.due_date.data
            )
            db.session.add(invoice)
            db.session.commit()
            flash('Invoice created successfully!', 'success')
            return redirect(url_for('staff.billing'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating invoice: {str(e)}', 'danger')

    invoices = Invoice.query.all()
    return render_template('billing.html', invoices=invoices, form=form)