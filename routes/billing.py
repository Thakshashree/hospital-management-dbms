from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Invoice, Patient
from extensions import db

billing_bp = Blueprint('billing', __name__)

@billing_bp.route('/')
def index():
    invoices = Invoice.query.all()
    return render_template('billing.html', invoices=invoices)

@billing_bp.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        invoice = Invoice(patient_id=request.form['patient_id'], 
                          total=float(request.form['total']),
                          status=request.form['status'])
        db.session.add(invoice)
        db.session.commit()
        return redirect(url_for('billing.index'))
    patients = Patient.query.all()
    return render_template('billing.html', add_mode=True, patients=patients)

@billing_bp.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    invoice = Invoice.query.get_or_404(id)
    db.session.delete(invoice)
    db.session.commit()
    return redirect(url_for('billing.index'))
