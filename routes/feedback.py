from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models import Feedback, Appointment
from extensions import db

feedback_bp = Blueprint('feedback', __name__)

@feedback_bp.route('/')
def index():
    feedbacks = Feedback.query.all()
    return render_template('feedback.html', feedbacks=feedbacks)

@feedback_bp.route('/<int:appointment_id>', methods=['GET', 'POST'])
def submit(appointment_id):
    if request.method == 'POST':
        rating = int(request.form['rating'])
        comment = request.form['comment']
        
        sentiment = "Neutral"
        try:
            model = current_app.gemini_model
            prompt = f"Analyze the sentiment of this feedback comment and reply with exactly one word (Positive, Negative, or Neutral): '{comment}'"
            response = model.generate_content(prompt)
            sentiment = response.text.strip().capitalize()
            if sentiment not in ["Positive", "Negative", "Neutral"]:
                sentiment = "Neutral"
        except Exception as e:
            print("Gemini error:", e)
            
        feedback = Feedback(appointment_id=appointment_id, rating=rating, comment=comment, sentiment=sentiment)
        db.session.add(feedback)
        db.session.commit()
        return redirect(url_for('feedback.index'))
        
    appointment = Appointment.query.get_or_404(appointment_id)
    return render_template('feedback.html', add_mode=True, appointment=appointment)

@feedback_bp.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    feedback = Feedback.query.get_or_404(id)
    db.session.delete(feedback)
    db.session.commit()
    return redirect(url_for('feedback.index'))