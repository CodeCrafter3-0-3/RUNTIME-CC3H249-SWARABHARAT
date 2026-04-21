from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from ai_engine import analyze_issue
from data_handler import save_report
import os

app = Flask(__name__)

@app.route('/whatsapp', methods=['POST'])
def whatsapp_reply():
    msg = request.form.get('Body', '').strip()
    from_number = request.form.get('From', '')
    
    resp = MessagingResponse()
    
    if not msg or msg.lower() in ['hi', 'hello', 'help']:
        resp.message('Describe your civic issue')
        return str(resp)
    
    try:
        analysis = analyze_issue(msg)
        save_report(analysis, msg, location=from_number)
        
        reply = f"Report submitted\nIssue: {analysis['issue']}\nUrgency: {analysis['urgency']}"
        resp.message(reply)
    except:
        resp.message("Error. Please try again.")
    
    return str(resp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
