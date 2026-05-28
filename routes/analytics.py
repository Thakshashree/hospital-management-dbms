from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import User, Appointment, Invoice, db
from datetime import datetime
from functools import wraps

analytics_bp = Blueprint('analytics', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role != 'admin':
            flash('Access denied. Admin only.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@analytics_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_patients = User.query.filter_by(role='patient').count()
    today = datetime.utcnow().date()
    
    # Replace these with actual queries if you have the models
    today_appointments = 0
    active_doctors = User.query.filter_by(role='doctor').count()
    revenue = 0
    
    return render_template(
        'admin_dashboard.html',
        user=current_user,
        total_patients=total_patients,
        today_appointments=today_appointments,
        active_doctors=active_doctors,
        revenue=revenue
    )