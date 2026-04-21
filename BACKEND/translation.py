from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

LANGUAGES = {
    'hi': 'Hindi', 'bn': 'Bengali', 'ta': 'Tamil', 'te': 'Telugu',
    'mr': 'Marathi', 'gu': 'Gujarati', 'kn': 'Kannada', 'ml': 'Malayalam',
    'pa': 'Punjabi', 'or': 'Odia'
}

def translate_text(text, target_lang='en'):
    try:
        lang_name = LANGUAGES.get(target_lang, 'English')
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"Translate to {lang_name}: {text}"}],
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except:
        return text

def detect_language(text):
    keywords = {
        'hi': ['है', 'में', 'का'], 'bn': ['আছে', 'এর'],
        'ta': ['உள்ளது', 'இல்'], 'te': ['ఉంది', 'లో']
    }
    for lang, words in keywords.items():
        if any(word in text for word in words):
            return lang
    return 'en'

def translate_ui(lang_code):
    translations = {
        'hi': {'submit': 'जमा करें', 'issue': 'समस्या', 'location': 'स्थान'},
        'ta': {'submit': 'சமர்ப்பிக்கவும்', 'issue': 'பிரச்சினை', 'location': 'இடம்'}
    }
    return translations.get(lang_code, {})
