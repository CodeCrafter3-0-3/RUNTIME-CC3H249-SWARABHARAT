import json
import random
from datetime import datetime, timedelta

TEMPLATES = {
    'Water': [
        "No water supply for {days} days in {location}",
        "Water is contaminated in {location}",
        "Water tanker not coming to {location}",
        "Broken water pipe in {location}",
        "Low water pressure in {location}"
    ],
    'Health': [
        "Hospital has no medicines in {location}",
        "Doctor not available at {location} clinic",
        "Ambulance not responding in {location}",
        "Medical emergency in {location}",
        "No beds available in {location} hospital"
    ],
    'Education': [
        "Teacher absent for {days} days in {location} school",
        "School building damaged in {location}",
        "No books available in {location} school",
        "Classroom has no electricity in {location}",
        "School toilet not working in {location}"
    ],
    'Safety': [
        "Street lights not working in {location}",
        "Road accident in {location}",
        "Crime increasing in {location}",
        "No police patrol in {location}",
        "Dangerous pothole in {location}"
    ],
    'Food': [
        "Ration shop closed in {location}",
        "Food quality poor in {location}",
        "PDS not distributing in {location}",
        "Expired food in {location} shop",
        "No rice available in {location}"
    ]
}

LOCATIONS = ['Delhi', 'Mumbai', 'Bangalore', 'Chennai', 'Kolkata', 'Hyderabad', 'Pune', 'Jaipur']
EMOTIONS = ['Fear', 'Distress', 'Calm', 'Anger']
URGENCIES = ['High', 'Medium', 'Low']

def generate_synthetic_reports(count=100):
    reports = []
    
    for i in range(count):
        issue = random.choice(list(TEMPLATES.keys()))
        template = random.choice(TEMPLATES[issue])
        location = random.choice(LOCATIONS)
        days = random.randint(1, 10)
        
        message = template.format(days=days, location=location)
        
        urgency = 'High' if days > 5 or 'emergency' in message.lower() else random.choice(URGENCIES)
        emotion = 'Fear' if urgency == 'High' else random.choice(EMOTIONS)
        
        report = {
            'id': f'syn_{i+1}',
            'message': message,
            'issue': issue,
            'emotion': emotion,
            'urgency': urgency,
            'summary': f"Citizen reports {issue.lower()} issue in {location}",
            'location': location,
            'time': (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
            'status': random.choice(['Submitted', 'In Progress', 'Resolved'])
        }
        reports.append(report)
    
    return reports

def save_synthetic_data(filename='synthetic_reports.json'):
    reports = generate_synthetic_reports(500)
    with open(filename, 'w') as f:
        for r in reports:
            f.write(json.dumps(r) + '\n')
    print(f"Generated {len(reports)} synthetic reports")
    return reports

if __name__ == '__main__':
    save_synthetic_data()
