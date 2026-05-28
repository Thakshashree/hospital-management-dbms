from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required
import datetime
from flask import current_app

pharmacy_bp = Blueprint('pharmacy', __name__)

def get_db():
    return current_app.get_db() # ← CHANGED: removed "from app import get_db"

def init_pharmacy_db():
    db = get_db()
    cur = db.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS pharmacy_inventory (
        id INT PRIMARY KEY AUTO_INCREMENT,
        med_name VARCHAR(100) NOT NULL,
        stock INT DEFAULT 0,
        expiry_date DATE NOT NULL,
        reorder_level INT DEFAULT 10
    )''')
    # Insert some sample data if empty
    cur.execute("SELECT COUNT(*) FROM pharmacy_inventory")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO pharmacy_inventory (med_name, stock, expiry_date, reorder_level) VALUES ('Paracetamol 500mg', 5, '2026-10-01', 50)")
        cur.execute("INSERT INTO pharmacy_inventory (med_name, stock, expiry_date, reorder_level) VALUES ('Amoxicillin 250mg', 100, '2026-06-15', 20)")
        cur.execute("INSERT INTO pharmacy_inventory (med_name, stock, expiry_date, reorder_level) VALUES ('Cough Syrup', 12, '2027-01-01', 15)")
    db.commit()
    db.close()

@pharmacy_bp.route('/pharmacy', methods=['GET', 'POST'])
def inventory():
    init_pharmacy_db()
    db = get_db()
    cur = db.cursor(dictionary=True)

    if request.method == 'POST':
        med_name = request.form.get('med_name')
        stock = request.form.get('stock')
        expiry = request.form.get('expiry_date')
        reorder = request.form.get('reorder_level', 10)
        try:
            cur.execute("INSERT INTO pharmacy_inventory (med_name, stock, expiry_date, reorder_level) VALUES (%s, %s, %s, %s)",
                        (med_name, stock, expiry, reorder))
            db.commit()
            flash('Medicine added to inventory successfully.', 'success')
        except Exception as e:
            flash(str(e), 'error')

    cur.execute("SELECT * FROM pharmacy_inventory ORDER BY expiry_date ASC")
    inventory = cur.fetchall()
    db.close()
    return render_template('pharmacy.html', inventory=inventory)

@pharmacy_bp.route('/pharmacy/ai-suggestions', methods=['POST'])
def ai_suggestions():
    gemini_model = current_app.gemini_model # ← CHANGED: Added this line
    init_pharmacy_db()
    db = get_db()
    cur = db.cursor(dictionary=True)
    # Find low stock or expiring within 30 days
    cur.execute("SELECT * FROM pharmacy_inventory WHERE stock <= reorder_level OR expiry_date <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)")
    alerts = cur.fetchall()
    db.close()

    if not alerts:
        return jsonify({"suggestion": "Inventory looks good. No reorders needed at this time."})

    prompt = "You are an AI pharmacy inventory assistant. Review these low-stock or soon-to-expire items and suggest a short, concise reorder plan (under 50 words):\n"
    for item in alerts:
        prompt += f"- {item['med_name']}: {item['stock']} left (Reorder level: {item['reorder_level']}), expires on {item['expiry_date']}\n"

    try:
        resp = gemini_model.generate_content(prompt)
        suggestion = resp.text.strip()
    except Exception as e:
        suggestion = "Error generating AI suggestion: " + str(e)

    return jsonify({"suggestion": suggestion, "alerts": alerts})