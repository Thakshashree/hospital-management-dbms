from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, DateField, TimeField, FloatField, IntegerField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError
import re

def strong_password(form, field):
    password = field.data
    if len(password) < 8:
        raise ValidationError('Password must be at least 8 characters.')
    if not re.search(r'[A-Z]', password):
        raise ValidationError('Password must contain at least one uppercase letter.')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-]', password):
        raise ValidationError('Password must contain at least one special character (!@#$%^&* etc).')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])


class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    name = StringField('Full Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), strong_password])


class PatientForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    name = StringField('Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), strong_password])
    dob = DateField('Date of Birth', validators=[DataRequired()])
    phone = StringField('Phone', validators=[DataRequired()])
    address = TextAreaField('Address', validators=[Optional()])
    blood_group = SelectField('Blood Group', choices=[('', '---'), ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('O+', 'O+'), ('O-', 'O-'), ('AB+', 'AB+'), ('AB-', 'AB-')], validators=[Optional()])
    emergency_contact = StringField('Emergency Contact', validators=[Optional()])


class DoctorForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    name = StringField('Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), strong_password])
    specialization = StringField('Specialization', validators=[DataRequired()])
    department = SelectField('Department', choices=[('Cardiology', 'Cardiology'), ('Neurology', 'Neurology'), ('Orthopedics', 'Orthopedics'), ('Pediatrics', 'Pediatrics'), ('General', 'General'), ('ENT', 'ENT')], validators=[DataRequired()])
    working_hours = StringField('Working Hours', validators=[DataRequired()])
    phone = StringField('Phone', validators=[DataRequired()])
    license_no = StringField('License No', validators=[DataRequired()])
    fee = FloatField('Consultation Fee', validators=[DataRequired()])


class RoomForm(FlaskForm):
    number = StringField('Room Number', validators=[DataRequired()])
    type = SelectField('Room Type', choices=[('General', 'General'), ('ICU', 'ICU'), ('Private', 'Private')], validators=[DataRequired()])


class LabReportForm(FlaskForm):
    patient_id = SelectField('Patient', coerce=int, validators=[DataRequired()])
    test_name = StringField('Test Name', validators=[DataRequired()])


class InvoiceForm(FlaskForm):
    patient_id = SelectField('Patient', coerce=int, validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    due_date = DateField('Due Date', validators=[DataRequired()])


class InventoryForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    min_stock = IntegerField('Min Stock Level', default=10)


class AppointmentForm(FlaskForm):
    patient_id = SelectField('Patient', coerce=int, validators=[Optional()])
    department = SelectField('Department', choices=[('', 'Select Department'), ('Cardiology', 'Cardiology'), ('Neurology', 'Neurology'), ('Orthopedics', 'Orthopedics'), ('Pediatrics', 'Pediatrics'), ('General', 'General'), ('ENT', 'ENT')], validators=[DataRequired()])
    doctor_id = SelectField('Doctor', coerce=int, validators=[DataRequired()])
    hospital_branch = SelectField('Hospital/Branch', choices=[('Main Branch', 'Main Branch'), ('Downtown Clinic', 'Downtown Clinic')], validators=[DataRequired()])
    appointment_type = SelectField('Appointment Type', choices=[('New consultation', 'New consultation'), ('Follow-up', 'Follow-up'), ('Emergency', 'Emergency'), ('Online', 'Online (Teleconsultation)')], validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    time = TimeField('Time', validators=[DataRequired()])
    reason = StringField('Short Reason for Visit', validators=[DataRequired()])
    symptoms = TextAreaField('Detailed Symptoms / Reason', validators=[Optional()])


class FeedbackForm(FlaskForm):
    rating = SelectField('Rating', choices=[(5, '5 - Excellent'), (4, '4 - Good'), (3, '3 - Average'), (2, '2 - Poor'), (1, '1 - Terrible')], coerce=int)
    comment = TextAreaField('Your Feedback', validators=[DataRequired()])


class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    new_password = PasswordField('New Password', validators=[DataRequired(), strong_password])
