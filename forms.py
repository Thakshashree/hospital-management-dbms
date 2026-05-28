from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, DateField, TimeField, FloatField, IntegerField
from wtforms.validators import DataRequired, Email, Length, Optional


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])


class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    name = StringField('Full Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])


class PatientForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    name = StringField('Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    dob = DateField('Date of Birth', validators=[DataRequired()])
    phone = StringField('Phone', validators=[DataRequired()])
    address = TextAreaField('Address', validators=[Optional()])
    blood_group = SelectField('Blood Group', choices=[('', '---'), ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('O+', 'O+'), ('O-', 'O-'), ('AB+', 'AB+'), ('AB-', 'AB-')], validators=[Optional()])
    emergency_contact = StringField('Emergency Contact', validators=[Optional()])


class DoctorForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    name = StringField('Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    specialization = StringField('Specialization', validators=[DataRequired()])
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
    doctor_id = SelectField('Doctor', coerce=int, validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    time = TimeField('Time', validators=[DataRequired()])
    reason = TextAreaField('Reason for Visit', validators=[DataRequired()])


class FeedbackForm(FlaskForm):
    rating = SelectField('Rating', choices=[(5, '5 - Excellent'), (4, '4 - Good'), (3, '3 - Average'), (2, '2 - Poor'), (1, '1 - Terrible')], coerce=int)
    comment = TextAreaField('Your Feedback', validators=[DataRequired()])


class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
