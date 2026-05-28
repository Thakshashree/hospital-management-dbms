from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required

beds_bp = Blueprint('beds', __name__)

def get_db():
    from app import get_db as gdb
    return gdb()

@beds_bp.route('/admin/beds')
def beds_dashboard():
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    # Get stats
    cur.execute("SELECT COUNT(*) as total FROM beds")
    total = cur.fetchone()['total']
    cur.execute("SELECT COUNT(*) as occupied FROM beds WHERE status='Occupied'")
    occupied = cur.fetchone()['occupied']
    cur.execute("SELECT COUNT(*) as vacant FROM beds WHERE status='Vacant'")
    vacant = cur.fetchone()['vacant']
    
    occupancy_rate = round((occupied / total * 100) if total > 0 else 0)
    
    # Get wards and beds
    cur.execute("SELECT * FROM wards")
    wards = cur.fetchall()
    
    cur.execute('''SELECT b.*, r.room_no, r.ward_id, p.name as patient_name 
                   FROM beds b 
                   JOIN rooms r ON b.room_id = r.id 
                   LEFT JOIN patients p ON b.patient_id = p.id''')
    all_beds = cur.fetchall()
    
    # Group beds by ward for UI display
    wards_data = []
    for w in wards:
        w_beds = [b for b in all_beds if b['ward_id'] == w['id']]
        wards_data.append({'ward': w, 'beds': w_beds})
        
    db.close()
    return render_template('beds.html', total=total, occupied=occupied, vacant=vacant, rate=occupancy_rate, wards_data=wards_data)

@beds_bp.route('/admin/beds/assign', methods=['POST'])
def assign_bed():
    bed_id = request.form.get('bed_id')
    patient_id = request.form.get('patient_id')
    
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("UPDATE beds SET status='Occupied', patient_id=%s, admitted_at=NOW() WHERE id=%s", (patient_id, bed_id))
        db.commit()
        flash("Bed assigned successfully", "success")
    except Exception as e:
        flash(str(e), "error")
    db.close()
    return redirect(url_for('beds.beds_dashboard'))

@beds_bp.route('/admin/beds/discharge', methods=['POST'])
def discharge_bed():
    bed_id = request.form.get('bed_id')
    
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("UPDATE beds SET status='Cleaning', patient_id=NULL, admitted_at=NULL WHERE id=%s", (bed_id,))
        db.commit()
        flash("Patient discharged. Bed sent for cleaning.", "success")
    except Exception as e:
        flash(str(e), "error")
    db.close()
    return redirect(url_for('beds.beds_dashboard'))

@beds_bp.route('/admin/beds/clean', methods=['POST'])
def clean_bed():
    bed_id = request.form.get('bed_id')
    
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("UPDATE beds SET status='Vacant' WHERE id=%s", (bed_id,))
        db.commit()
        flash("Bed marked as Vacant.", "success")
    except Exception as e:
        flash(str(e), "error")
    db.close()
    return redirect(url_for('beds.beds_dashboard'))
