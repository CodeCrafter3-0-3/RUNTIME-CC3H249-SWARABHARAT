import os
from datetime import datetime

class MonitoringSystem:
    def __init__(self):
        self.metrics = {
            'total_requests': 0,
            'errors': 0,
            'avg_response_time': 0,
            'active_users': 0
        }
        self.alerts = []
    
    def log_request(self, endpoint, response_time, status_code):
        self.metrics['total_requests'] += 1
        
        if status_code >= 400:
            self.metrics['errors'] += 1
            if self.metrics['errors'] > 100:
                self.create_alert('high_error_rate', f"Error rate: {self.metrics['errors']}")
        
        # Update avg response time
        current_avg = self.metrics['avg_response_time']
        self.metrics['avg_response_time'] = (current_avg * 0.9) + (response_time * 0.1)
        
        if self.metrics['avg_response_time'] > 1000:
            self.create_alert('slow_response', f"Avg response time: {self.metrics['avg_response_time']}ms")
    
    def create_alert(self, alert_type, message):
        alert = {
            'type': alert_type,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'severity': 'high' if 'error' in alert_type else 'medium'
        }
        self.alerts.append(alert)
        
        # Keep only last 100 alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
        return alert
    
    def get_health_status(self):
        error_rate = self.metrics['errors'] / max(self.metrics['total_requests'], 1)
        
        if error_rate > 0.1:
            status = 'critical'
        elif error_rate > 0.05:
            status = 'warning'
        else:
            status = 'healthy'
        
        return {
            'status': status,
            'metrics': self.metrics,
            'recent_alerts': self.alerts[-10:],
            'error_rate': round(error_rate * 100, 2)
        }

monitor = MonitoringSystem()
