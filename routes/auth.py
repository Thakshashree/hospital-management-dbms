from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user
from models import User, Patient
from forms import LoginForm, ForgotPasswordForm
from extensions import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form.get('role')
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        age = request.form.get('age')
        gender = request.form.get('gender')
        
        staff_role = request.form.get('staff_role') if role == 'staff' else None
        department = request.form.get('department') if role == 'staff' else None
        staff_id = request.form.get('staff_id') if role == 'staff' else None

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.register'))

        user = User(email=email, name=name, role=role, age=age, gender=gender,
                    staff_role=staff_role, department=department, staff_id=staff_id)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        if role == 'patient':
            patient = Patient(user_id=user.id)
            db.session.add(patient)
            db.session.commit()

        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password reset successfully. You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Email not found.', 'danger')
    return render_template('forgot_password.html', form=form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))