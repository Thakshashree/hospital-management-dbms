from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Inventory
from extensions import db

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/')
def index():
    items = Inventory.query.all()
    return render_template('inventory.html', items=items)

@inventory_bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        item = Inventory(name=request.form['name'], 
                         quantity=int(request.form['quantity']), 
                         reorder_level=int(request.form['reorder_level']))
        db.session.add(item)
        db.session.commit()
        return redirect(url_for('inventory.index'))
    return render_template('inventory.html', add_mode=True)

@inventory_bp.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    item = Inventory.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('inventory.index'))
