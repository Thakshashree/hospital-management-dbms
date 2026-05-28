from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Doctor
from extensions import db

doctor_bp = Blueprint('doctor', __name__)

@doctor_bp.route('/')
def index():
    doctors = Doctor.query.all()
    return render_template('doctors.html', doctors=doctors)

@doctor_bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        doctor = Doctor(name=request.form['name'], 
                        specialization=request.form['specialization'], 
                        phone=request.form['phone'])
        db.session.add(doctor)
        db.session.commit()
        return redirect(url_for('doctor.index'))
    return render_template('doctors.html', add_mode=True)

@doctor_bp.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    doctor = Doctor.query.get_or_404(id)
    db.session.delete(doctor)
    db.session.commit()
    return redirect(url_for('doctor.index'))
