from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from models import Appointment, Patient, Doctor
from extensions import db
import json

appointment_bp = Blueprint('appointment', __name__)

@appointment_bp.route('/')
def index():
    appointments = Appointment.query.all()
    return render_template('appointments.html', appointments=appointments)

@appointment_bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        appt = Appointment(patient_id=request.form['patient_id'], 
                           doctor_id=request.form['doctor_id'], 
                           date=request.form['date'],
                           time=request.form['time'])
        db.session.add(appt)
        db.session.commit()
        return redirect(url_for('appointment.index'))
    patients = Patient.query.all()
    doctors = Doctor.query.all()
    return render_template('appointments.html', add_mode=True, patients=patients, doctors=doctors)

@appointment_bp.route('/voice')
def voice():
    return render_template('voice_booking.html')

@appointment_bp.route('/voice-process', methods=['POST'])
def voice_process():
    data = request.json
    transcript = data.get('transcript', '')
    
    if not transcript:
        return jsonify({'error': 'No transcript provided'}), 400
        
    try:
        model = current_app.gemini_model
        prompt = f"""
        Extract the following information from this transcript to book a medical appointment:
        Transcript: "{transcript}"
        
        Return ONLY a JSON object with these keys (use null if not found):
        - patient_name (string)
        - doctor_name (string)
        - date (string, YYYY-MM-DD format if possible, otherwise what they said)
        - time (string, HH:MM format if possible, otherwise what they said)
        """
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith('```json'):
            text = text[7:]
        if text.endswith('```'):
            text = text[:-3]
            
        parsed = json.loads(text.strip())
        
        # Try to match patient and doctor
        patient = Patient.query.filter(Patient.name.ilike(f"%{parsed.get('patient_name', '')}%")).first()
        doctor = Doctor.query.filter(Doctor.name.ilike(f"%{parsed.get('doctor_name', '')}%")).first()
        
        if not patient or not doctor:
            return jsonify({'error': 'Could not match patient or doctor from database', 'parsed': parsed}), 400
            
        appt = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            date=parsed.get('date', ''),
            time=parsed.get('time', '')
        )
        db.session.add(appt)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Appointment booked successfully via Voice!'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@appointment_bp.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    appt = Appointment.query.get_or_404(id)
    db.session.delete(appt)
    db.session.commit()
    return redirect(url_for('appointment.index'))
