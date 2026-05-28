from flask import Blueprint, render_template, request, flash
from flask_login import login_required
from flask import current_app

summary_bp = Blueprint('summary', __name__)

def get_db():
    return current_app.get_db()  # ← CHANGED: removed "from app import get_db"

@summary_bp.route('/doctor/patient-summary/<int:patient_id>')
def patient_summary(patient_id):
    gemini_model = current_app.gemini_model  # ← CHANGED: Added this line
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    cur.execute("SELECT * FROM patients WHERE id=%s", (patient_id,))
    patient = cur.fetchone()
    
    if not patient:
        flash("Patient not found", "error")
        db.close()
        return render_template('patient_summary.html', patient=None)
        
    cur.execute("SELECT a.*, d.name as doctor_name, d.specialization FROM appointments a JOIN doctors d ON a.doctor_id = d.id WHERE a.patient_id=%s ORDER BY appt_date DESC LIMIT 5", (patient_id,))
    appts = cur.fetchall()
    
    cur.execute("SELECT * FROM prescriptions WHERE appointment_id IN (SELECT id FROM appointments WHERE patient_id=%s)", (patient_id,))
    prescriptions = cur.fetchall()
    
    db.close()
    
    data_str = f"Patient Name: {patient['name']}, Age: {patient.get('age', 'Unknown')}\n\nRecent Appointments:\n"
    for a in appts:
        data_str += f"- Date: {a['appt_date']}, Dr. {a['doctor_name']} ({a['specialization']}). Notes/Symptoms: {a.get('notes', 'None')}\n"
        
    data_str += "\nPrescriptions:\n"
    for p in prescriptions:
        data_str += f"- {p.get('medicine', 'Medicine')} ({p.get('dosage', 'Dosage')})\n"
        
    try:
        prompt = f"You are an AI medical assistant for a doctor. Summarize this patient's medical history in 3 concise bullet points for quick reading before a consultation:\n\n{data_str}"
        resp = gemini_model.generate_content(prompt)
        ai_summary = resp.text
    except Exception as e:
        ai_summary = "Error generating summary: " + str(e)
        
    return render_template('patient_summary.html', patient=patient, ai_summary=ai_summary, appts=appts, prescriptions=prescriptions)