from flask_socketio import SocketIO, emit
from flask import request

socketio = None

def init_socketio(app):
    global socketio
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    @socketio.on('connect')
    def handle_connect():
        print(f'Client connected: {request.sid}')
        emit('connected', {'message': 'Connected to SwaraBharat real-time'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        print(f'Client disconnected: {request.sid}')
    
    return socketio

def broadcast_new_report(report):
    if socketio:
        socketio.emit('new_report', {
            'id': report.get('id'),
            'issue': report.get('issue'),
            'urgency': report.get('urgency'),
            'location': report.get('location'),
            'time': report.get('time')
        })

def broadcast_alert(alert_type, message, data=None):
    if socketio:
        socketio.emit('alert', {
            'type': alert_type,
            'message': message,
            'data': data
        })
