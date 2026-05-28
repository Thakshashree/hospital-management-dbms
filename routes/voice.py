from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
import json
from flask import current_app  # ← CHANGED: removed "from app import get_db, gemini_model"

voice_bp = Blueprint('voice', __name__)

def get_db():
    return current_app.get_db()  # ← ADDED: use current_app instead of import

@voice_bp.route('/voice-booking')
def voice_booking_page():
    return render_template('voice_booking.html')

@voice_bp.route('/api/voice-nlp', methods=['POST'])
def process_voice_nlp():
    gemini_model = current_app.gemini_model  # ← ADDED: get model from current_app
    data = request.json
    transcript = data.get('transcript', '')
    
    # Send transcript to Gemini to extract intent and entities
    prompt = f"""
    You are an AI NLU (Natural Language Understanding) system for a hospital booking app.
    A patient just said this via voice: "{transcript}"
    
    Extract the following information if present, and return a STRICT JSON object:
    - intent: "book_appointment", "cancel_appointment", or "unknown"
    - department: Medical specialty (e.g., Cardiology, General, Dental) or null
    - date: Date mentioned (e.g., "tomorrow", "next Monday", "2026-10-15") or null
    - time: Time mentioned (e.g., "morning", "10 AM") or null
    
    Output ONLY valid JSON.
    """
    
    try:
        resp = gemini_model.generate_content(prompt)
        text_resp = resp.text.strip()
        # Clean up markdown if present
        if text_resp.startswith("```json"):
            text_resp = text_resp.replace("```json\n", "").replace("\n```", "")
        
        parsed = json.loads(text_resp)
    except Exception as e:
        parsed = {"intent": "unknown", "error": str(e)}
        
    return jsonify(parsed)