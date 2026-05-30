from flask import Flask, render_template, redirect, url_for
from flask_login import UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, time
from extensions import db, login_manager, csrf

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config['SECRET_KEY'] = 'dev-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
    app.config['UPLOAD_FOLDER'] = 'uploads'
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = 'auth.login'
    
    from routes.auth import auth_bp
    from routes.staff import staff_bp
    from routes.patient import patient_bp
    from routes.public import public_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(public_bp)
    # Note: doctor_bp, appointment_bp, room_bp, lab_bp, inventory_bp, feedback_bp
    # are intentionally NOT registered here — all those routes now live in staff_bp.
    
    with app.app_context():
        db.create_all()
        if not User.query.first():
            staff = User(email='staff@test.com', name='Admin Staff', role='staff')
            staff.set_password('123456')
            patient = User(email='patient@test.com', name='John Patient', role='patient')
            patient.set_password('123456')
            doctor = User(email='doc@test.com', name='Dr Smith', role='staff')
            doctor.set_password('123456')
            db.session.add_all([staff, patient, doctor])
            db.session.commit()
            
            db.session.add(Patient(user_id=patient.id, dob=date(1990,1,1), phone='9999999999'))
            db.session.add(Doctor(user_id=doctor.id, specialization='General', fee=500))
            db.session.add(Room(number='101', type='General'))
            db.session.commit()
            
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.role == 'staff': 
                return redirect(url_for('staff.dashboard'))
            return redirect(url_for('patient.dashboard'))
        return redirect(url_for('auth.login'))
        
    return app

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    staff_role = db.Column(db.String(50))
    department = db.Column(db.String(50))
    staff_id = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password): 
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password): 
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id): 
    return User.query.get(int(user_id))

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    dob = db.Column(db.Date)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    blood_group = db.Column(db.String(5))
    emergency_contact = db.Column(db.String(20))
    user = db.relationship('User', backref='patient_profile')

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    department = db.Column(db.String(100))
    specialization = db.Column(db.String(100))
    working_hours = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    license_no = db.Column(db.String(50))
    fee = db.Column(db.Float)
    status = db.Column(db.String(20), default='Active')
    user = db.relationship('User', backref='doctor_profile')

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    department = db.Column(db.String(100))
    hospital_branch = db.Column(db.String(100))
    appointment_type = db.Column(db.String(50))
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    reason = db.Column(db.Text)
    symptoms = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    patient = db.relationship('User', foreign_keys=[patient_id])
    doctor = db.relationship('User', foreign_keys=[doctor_id])

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(10), unique=True)
    type = db.Column(db.String(20))
    status = db.Column(db.String(20), default='Vacant')
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    admitted_at = db.Column(db.DateTime)

class LabReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    test_name = db.Column(db.String(100))
    file_path = db.Column(db.String(255))
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    patient = db.relationship('User', foreign_keys=[patient_id])
    doctor = db.relationship('User', foreign_keys=[doctor_id])

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Float)
    description = db.Column(db.String(200))
    status = db.Column(db.String(20), default='Unpaid')
    due_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    patient = db.relationship('User', foreign_keys=[patient_id])

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    quantity = db.Column(db.Integer)
    expiry_date = db.Column(db.Date)
    supplier = db.Column(db.String(100))
    category = db.Column(db.String(50))
    min_stock = db.Column(db.Integer, default=10)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    patient_name = db.Column(db.String(100))
    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)
    status = db.Column(db.String(20), default='Open')
    created_at = db.Column(db.DateTime, default=datetime.now)
    patient = db.relationship('User', foreign_keys=[patient_id])

class MedicalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    diagnosis = db.Column(db.Text)
    prescription = db.Column(db.Text)
    notes = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    patient = db.relationship('User', foreign_keys=[patient_id])
    doctor = db.relationship('User', foreign_keys=[doctor_id])

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', foreign_keys=[user_id])