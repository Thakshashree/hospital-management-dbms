from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

portal_bp = Blueprint('portal', __name__)

def get_db():
    from app import get_db as gdb
    return gdb()

@portal_bp.route('/my')
@login_required
def my_dashboard():
    db = get_db()
    cur = db.cursor(dictionary=True)
    pid = current_user.patient_id
    cur.execute("SELECT * FROM patients WHERE id=%s", (pid,))
    patient = cur.fetchone()
    cur.execute("SELECT a.*, d.name as doctor_name, d.specialization FROM appointments a JOIN doctors d ON a.doctor_id=d.id WHERE a.patient_id=%s ORDER BY a.appt_date DESC LIMIT 5", (pid,))
    appts = cur.fetchall()
    cur.execute("SELECT * FROM bill_master WHERE patient_id=%s ORDER BY created_at DESC LIMIT 5", (pid,))
    bills = cur.fetchall()
    cur.execute("SELECT * FROM insurance_claims WHERE patient_id=%s ORDER BY created_at DESC LIMIT 5", (pid,))
    claims = cur.fetchall()
    db.close()
    return render_template('portal_dashboard.html', patient=patient, appointments=appts, bills=bills, claims=claims)

@portal_bp.route('/my/profile')
@login_required
def my_profile():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM patients WHERE id=%s", (current_user.patient_id,))
    patient = cur.fetchone()
    cur.execute("SELECT pi.*, ip.name as provider_name FROM patient_insurance pi LEFT JOIN insurance_providers ip ON pi.provider_id=ip.id WHERE pi.patient_id=%s", (current_user.patient_id,))
    insurance = cur.fetchone()
    cur.execute("SELECT * FROM digital_health_cards WHERE patient_id=%s", (current_user.patient_id,))
    card = cur.fetchone()
    db.close()
    return render_template('portal_profile.html', patient=patient, insurance=insurance, card=card)

@portal_bp.route('/my/appointments')
@login_required
def my_appointments():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT a.*, d.name as doctor_name, d.specialization FROM appointments a JOIN doctors d ON a.doctor_id=d.id WHERE a.patient_id=%s ORDER BY a.appt_date DESC", (current_user.patient_id,))
    appts = cur.fetchall()
    db.close()
    return render_template('portal_appointments.html', appointments=appts)

@portal_bp.route('/my/bills')
@login_required
def my_bills():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM bill_master WHERE patient_id=%s ORDER BY created_at DESC", (current_user.patient_id,))
    bills = cur.fetchall()
    db.close()
    return render_template('portal_bills.html', bills=bills)

@portal_bp.route('/my/claims')
@login_required
def my_claims():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT ic.*, ip.name as provider_name FROM insurance_claims ic LEFT JOIN patient_insurance pi ON ic.policy_id=pi.id LEFT JOIN insurance_providers ip ON pi.provider_id=ip.id WHERE ic.patient_id=%s ORDER BY ic.created_at DESC", (current_user.patient_id,))
    claims = cur.fetchall()
    db.close()
    return render_template('portal_claims.html', claims=claims)
