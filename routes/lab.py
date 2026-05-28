from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from models import LabReport, Patient
from extensions import db
import os
import google.generativeai as genai

lab_bp = Blueprint('lab', __name__)

@lab_bp.route('/')
def index():
    reports = LabReport.query.all()
    return render_template('lab.html', reports=reports)

@lab_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            summary = "Summary generation failed or not an image."
            try:
                # Assuming gemini-1.5-flash can handle this (we need to upload it or pass file content)
                # For simplicity in this demo, if it's an image we process it, or just use text if possible
                # The prompt requested Gemini Vision, let's use the file directly
                
                model = current_app.gemini_model
                
                # Gemini requires uploading the file or passing the PIL image. 
                # To keep it simple and robust without extra dependencies like PIL or PyPDF2:
                sample_file = genai.upload_file(path=filepath)
                response = model.generate_content(["Summarize this lab report in 2-3 sentences. Mention key values if any.", sample_file])
                summary = response.text
            except Exception as e:
                summary = f"Error generating summary: {str(e)}"
            
            report = LabReport(patient_id=request.form['patient_id'], filename=filename, summary=summary)
            db.session.add(report)
            db.session.commit()
            return redirect(url_for('lab.index'))
            
    patients = Patient.query.all()
    return render_template('lab.html', add_mode=True, patients=patients)

@lab_bp.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    report = LabReport.query.get_or_404(id)
    db.session.delete(report)
    db.session.commit()
    return redirect(url_for('lab.index'))