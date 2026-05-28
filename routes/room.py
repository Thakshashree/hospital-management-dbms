from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Room, Patient
from extensions import db

room_bp = Blueprint('room', __name__)

@room_bp.route('/')
def index():
    rooms = Room.query.all()
    patients = Patient.query.all()
    return render_template('rooms.html', rooms=rooms, patients=patients)

@room_bp.route('/assign/<int:id>', methods=['POST'])
def assign(id):
    room = Room.query.get_or_404(id)
    patient_id = request.form.get('patient_id')
    if patient_id:
        room.patient_id = patient_id
        room.status = 'Occupied'
        db.session.commit()
    return redirect(url_for('room.index'))

@room_bp.route('/discharge/<int:id>', methods=['POST'])
def discharge(id):
    room = Room.query.get_or_404(id)
    room.patient_id = None
    room.status = 'Available'
    db.session.commit()
    return redirect(url_for('room.index'))
