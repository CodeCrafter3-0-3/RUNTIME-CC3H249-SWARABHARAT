from data_handler import read_reports
from collections import defaultdict

def generate_heatmap_data():
    reports = read_reports()
    location_data = defaultdict(lambda: {'count': 0, 'high_urgency': 0, 'issues': {}})
    
    for r in reports:
        loc = r.get('location', 'Unknown')
        if loc and loc != 'Unknown':
            location_data[loc]['count'] += 1
            if r.get('urgency') == 'High':
                location_data[loc]['high_urgency'] += 1
            issue = r.get('issue', 'Other')
            location_data[loc]['issues'][issue] = location_data[loc]['issues'].get(issue, 0) + 1
    
    heatmap = []
    for loc, data in location_data.items():
        heatmap.append({
            'location': loc,
            'lat': 28.6139 + (hash(loc) % 100) / 1000,
            'lng': 77.2090 + (hash(loc) % 100) / 1000,
            'count': data['count'],
            'high_urgency': data['high_urgency'],
            'intensity': min(data['count'] / 10, 1.0),
            'top_issue': max(data['issues'], key=data['issues'].get) if data['issues'] else 'Other'
        })
    
    return sorted(heatmap, key=lambda x: x['count'], reverse=True)

def get_hotspots(threshold=5):
    heatmap = generate_heatmap_data()
    return [h for h in heatmap if h['count'] >= threshold]

def get_clusters():
    heatmap = generate_heatmap_data()
    clusters = []
    for h in heatmap:
        if h['count'] >= 3:
            clusters.append({
                'center': {'lat': h['lat'], 'lng': h['lng']},
                'radius': h['count'] * 100,
                'issues': h['count'],
                'urgency': 'High' if h['high_urgency'] > h['count'] / 2 else 'Medium'
            })
    return clusters
