from flask import Blueprint, render_template, request, jsonify
import datetime
from flask import current_app  # ← CHANGED: removed "from app import get_db, gemini_model"

reminder_bp = Blueprint('reminder', __name__)

def get_db():
    return current_app.get_db()  # ← ADDED: use current_app instead of import

@reminder_bp.route('/admin/reminders')
def ai_reminders():
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    # Get upcoming appointments for tomorrow
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    cur.execute('''SELECT a.*, p.name as patient_name, p.phone, d.name as doctor_name 
                   FROM appointments a 
                   JOIN patients p ON a.patient_id = p.id 
                   JOIN doctors d ON a.doctor_id = d.id 
                   WHERE a.appt_date = %s AND a.status = 'Scheduled' ''', (tomorrow,))
    upcoming = cur.fetchall()
    db.close()
    
    return render_template('reminder.html', upcoming=upcoming, tomorrow=tomorrow)

@reminder_bp.route('/admin/generate-reminder', methods=['POST'])
def generate_reminder():
    gemini_model = current_app.gemini_model  # ← ADDED: get model from current_app
    data = request.json
    patient_name = data.get('patient_name')
    doctor_name = data.get('doctor_name')
    time = data.get('time', 'Morning')
    date = data.get('date')
    
    prompt = f"You are an AI assistant for MediVault Pro hospital. Generate a short, polite, and friendly SMS reminder (under 160 characters) for a patient named {patient_name} who has an appointment with Dr. {doctor_name} on {date} at {time}."
    
    try:
        resp = gemini_model.generate_content(prompt)
        msg = resp.text.strip()
    except Exception as e:
        msg = f"Reminder: Dear {patient_name}, you have an appointment with Dr. {doctor_name} on {date} at {time}. Please arrive 10 mins early."
        
    return jsonify({"message": msg})