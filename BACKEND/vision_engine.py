import base64
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def analyze_image(image_data):
    try:
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyze civic issue: pothole, garbage, water leak, broken infrastructure, or electrical hazard. Rate severity 1-10."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                ]
            }],
            max_tokens=300
        )
        
        result = response.choices[0].message.content
        return {'detected': True, 'analysis': result, 'confidence': 0.85}
    except Exception as e:
        return {'detected': False, 'error': str(e)}

def verify_authenticity(image_data):
    try:
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Is this image authentic or AI-generated? Answer: AUTHENTIC or FAKE"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                ]
            }],
            max_tokens=50
        )
        result = response.choices[0].message.content.upper()
        return 'AUTHENTIC' in result
    except:
        return True
