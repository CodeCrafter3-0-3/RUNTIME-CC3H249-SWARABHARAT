from datetime import datetime, timedelta
from collections import defaultdict
import statistics

class TimeSeriesForecaster:
    def forecast_next_week(self, reports):
        if len(reports) < 7:
            return {'error': 'Need at least 7 days of data'}
        
        # Group by day
        daily_counts = defaultdict(int)
        for r in reports:
            try:
                date = datetime.fromisoformat(r.get('time', '')).date()
                daily_counts[date] += 1
            except:
                continue
        
        if not daily_counts:
            return {'error': 'Insufficient data'}
        
        # Calculate trend
        counts = [daily_counts[d] for d in sorted(daily_counts.keys())]
        avg = statistics.mean(counts)
        trend = (counts[-1] - counts[0]) / len(counts) if len(counts) > 1 else 0
        
        # Forecast next 7 days
        forecast = []
        for i in range(1, 8):
            predicted = max(0, int(avg + (trend * i)))
            forecast.append({
                'day': i,
                'predicted_count': predicted,
                'confidence': min(90, 60 + len(counts) * 2)
            })
        
        return {
            'forecast': forecast,
            'current_avg': round(avg, 1),
            'trend': 'increasing' if trend > 0 else 'decreasing' if trend < 0 else 'stable'
        }
    
    def detect_seasonality(self, reports):
        hour_counts = defaultdict(int)
        day_counts = defaultdict(int)
        
        for r in reports:
            try:
                dt = datetime.fromisoformat(r.get('time', ''))
                hour_counts[dt.hour] += 1
                day_counts[dt.strftime('%A')] += 1
            except:
                continue
        
        peak_hour = max(hour_counts, key=hour_counts.get) if hour_counts else 12
        peak_day = max(day_counts, key=day_counts.get) if day_counts else 'Monday'
        
        return {
            'peak_hour': peak_hour,
            'peak_day': peak_day,
            'hourly_pattern': dict(hour_counts),
            'daily_pattern': dict(day_counts)
        }
    
    def calculate_velocity(self, reports):
        if len(reports) < 2:
            return {'velocity': 0, 'acceleration': 0}
        
        # Last 24 hours vs previous 24 hours
        now = datetime.now()
        last_24h = [r for r in reports if (now - datetime.fromisoformat(r.get('time', now.isoformat()))).days < 1]
        prev_24h = [r for r in reports if 1 <= (now - datetime.fromisoformat(r.get('time', now.isoformat()))).days < 2]
        
        velocity = len(last_24h) - len(prev_24h)
        acceleration = velocity / len(prev_24h) if prev_24h else 0
        
        return {
            'velocity': velocity,
            'acceleration': round(acceleration * 100, 1),
            'status': 'accelerating' if velocity > 0 else 'decelerating' if velocity < 0 else 'steady'
        }

forecaster = TimeSeriesForecaster()
