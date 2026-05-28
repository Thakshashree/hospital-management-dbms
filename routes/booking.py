from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
import datetime, json

booking_bp = Blueprint('booking', __name__)

def get_db():
    from app import get_db as gdb
    return gdb()

@booking_bp.route('/book-smart', methods=['GET', 'POST'])
def book_smart():
    db = get_db()
    cur = db.cursor(dictionary=True)
    step = request.args.get('step', '1')
    if request.method == 'POST' and step == '1':
        symptoms = request.form.get('symptoms', '')
        try:
            from app import gemini_model
            resp = gemini_model.generate_content(f"Based on these symptoms: {symptoms}, suggest ONE medical specialization (e.g., Cardiology, Orthopedics, Dermatology, General Medicine, Neurology, ENT, Ophthalmology, Pediatrics). Reply with ONLY the specialization name, nothing else.")
            spec = resp.text.strip()
        except:
            spec = 'General Medicine'
        cur.execute("SELECT * FROM doctors WHERE specialization LIKE %s", (f'%{spec}%',))
        docs = cur.fetchall()
        if not docs:
            cur.execute("SELECT * FROM doctors")
            docs = cur.fetchall()
        db.close()
        return render_template('book_smart.html', step='2', symptoms=symptoms, specialization=spec, doctors=docs)
    if request.method == 'POST' and step == '2':
        doctor_id = request.form.get('doctor_id')
        appt_date = request.form.get('appt_date')
        appt_time = request.form.get('appt_time', '09:00')
        symptoms = request.form.get('symptoms', '')
        patient_id = current_user.patient_id if current_user.is_authenticated else request.form.get('patient_id', 1)
        try:
            cur.execute("INSERT INTO appointments (patient_id, doctor_id, appt_date, status, notes) VALUES (%s,%s,%s,'Scheduled',%s)",
                        (patient_id, doctor_id, appt_date, symptoms))
            appt_id = cur.lastrowid
            cur.execute("SELECT COALESCE(MAX(token_number),0)+1 as next_token FROM queue_tokens qt JOIN appointments a ON qt.appointment_id=a.id WHERE a.doctor_id=%s AND a.appt_date=%s",
                        (doctor_id, appt_date))
            token = cur.fetchone()['next_token']
            cur.execute("INSERT INTO queue_tokens (appointment_id, token_number, status, estimated_time) VALUES (%s,%s,'Waiting',%s)",
                        (appt_id, token, appt_time))
            db.commit()
            flash(f'Appointment booked! Your token number is {token}', 'success')
        except Exception as e:
            flash(str(e), 'error')
        db.close()
        return redirect(url_for('booking.book_smart'))
    # GET step 1
    db.close()
    return render_template('book_smart.html', step='1')

@booking_bp.route('/queue/live/<int:doctor_id>')
def queue_live(doctor_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    today = datetime.date.today()
    cur.execute("""SELECT qt.*, p.name as patient_name FROM queue_tokens qt
        JOIN appointments a ON qt.appointment_id=a.id
        JOIN patients p ON a.patient_id=p.id
        WHERE a.doctor_id=%s AND a.appt_date=%s ORDER BY qt.token_number""", (doctor_id, today))
    tokens = cur.fetchall()
    current = next((t for t in tokens if t['status'] == 'In Consultation'), None)
    waiting = [t for t in tokens if t['status'] == 'Waiting']
    db.close()
    return jsonify({'current': {'token': current['token_number'], 'patient': current['patient_name']} if current else None,
                    'waiting_count': len(waiting),
                    'next_token': waiting[0]['token_number'] if waiting else None})

@booking_bp.route('/queue/display/<int:doctor_id>')
def queue_display(doctor_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT name, specialization FROM doctors WHERE id=%s", (doctor_id,))
    doctor = cur.fetchone()
    today = datetime.date.today()
    cur.execute("""SELECT qt.*, p.name as patient_name FROM queue_tokens qt
        JOIN appointments a ON qt.appointment_id=a.id
        JOIN patients p ON a.patient_id=p.id
        WHERE a.doctor_id=%s AND a.appt_date=%s ORDER BY qt.token_number""", (doctor_id, today))
    tokens = cur.fetchall()
    db.close()
    return render_template('queue_display.html', doctor=doctor, doctor_id=doctor_id, tokens=tokens)

@booking_bp.route('/queue/call-next', methods=['POST'])
def queue_call_next():
    doctor_id = request.form.get('doctor_id') or request.json.get('doctor_id')
    today = datetime.date.today()
    db = get_db()
    cur = db.cursor(dictionary=True)
    # Complete current
    cur.execute("""UPDATE queue_tokens qt JOIN appointments a ON qt.appointment_id=a.id
        SET qt.status='Completed' WHERE a.doctor_id=%s AND a.appt_date=%s AND qt.status='In Consultation'""", (doctor_id, today))
    # Call next waiting
    cur.execute("""SELECT qt.id FROM queue_tokens qt JOIN appointments a ON qt.appointment_id=a.id
        WHERE a.doctor_id=%s AND a.appt_date=%s AND qt.status='Waiting' ORDER BY qt.token_number LIMIT 1""", (doctor_id, today))
    nxt = cur.fetchone()
    if nxt:
        cur.execute("UPDATE queue_tokens SET status='In Consultation', called_at=NOW() WHERE id=%s", (nxt['id'],))
    db.commit()
    db.close()
    return jsonify({'success': True, 'called': nxt['id'] if nxt else None})

@booking_bp.route('/api/slots/<int:doctor_id>/<date>')
def get_slots(doctor_id, date):
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        dt = datetime.datetime.strptime(date, '%Y-%m-%d')
        dow = dt.isoweekday()
        cur.execute("SELECT * FROM doctor_availability WHERE doctor_id=%s AND day_of_week=%s", (doctor_id, dow))
        avail = cur.fetchone()
        if not avail:
            db.close()
            return jsonify({'slots': []})
        cur.execute("SELECT TIME(notes) as booked_time FROM appointments WHERE doctor_id=%s AND appt_date=%s", (doctor_id, date))
        booked = [r['booked_time'] for r in cur.fetchall() if r['booked_time']]
        start = datetime.datetime.combine(dt.date(), datetime.time()) + datetime.timedelta(hours=avail['start_time'].seconds // 3600, minutes=(avail['start_time'].seconds % 3600) // 60) if isinstance(avail['start_time'], datetime.timedelta) else datetime.datetime.combine(dt.date(), avail['start_time'])
        end = datetime.datetime.combine(dt.date(), datetime.time()) + datetime.timedelta(hours=avail['end_time'].seconds // 3600, minutes=(avail['end_time'].seconds % 3600) // 60) if isinstance(avail['end_time'], datetime.timedelta) else datetime.datetime.combine(dt.date(), avail['end_time'])
        dur = avail['slot_duration_minutes']
        slots = []
        while start < end:
            t = start.strftime('%H:%M')
            slots.append({'time': t, 'available': True})
            start += datetime.timedelta(minutes=dur)
        db.close()
        return jsonify({'slots': slots})
    except Exception as e:
        db.close()
        return jsonify({'slots': [], 'error': str(e)})
