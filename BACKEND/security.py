import bcrypt
import re
import html
from functools import wraps
from flask import request, jsonify

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def sanitize_input(text):
    if text is None:
        return text

    if isinstance(text, str):
        text = html.escape(text)
        text = re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        return text.strip()

    if isinstance(text, dict):
        return {k: sanitize_input(v) for k, v in text.items()}

    if isinstance(text, list):
        return [sanitize_input(v) for v in text]

    return text

def validate_input(data, required_fields):
    errors = []
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"{field} is required")
    return errors

def rate_limit_strict(max_requests=10, window=60):
    from time import time
    requests_log = {}
    
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            ip = request.remote_addr or 'unknown'
            now = time()
            
            if ip not in requests_log:
                requests_log[ip] = []
            
            requests_log[ip] = [t for t in requests_log[ip] if now - t < window]
            
            if len(requests_log[ip]) >= max_requests:
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            requests_log[ip].append(now)
            return f(*args, **kwargs)
        return wrapper
    return decorator

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    pattern = r'^\+?[1-9]\d{9,14}$'
    return re.match(pattern, phone) is not None
