import re
from collections import Counter

class AdvancedNLP:
    def __init__(self):
        self.sentiment_words = {
            'positive': ['good', 'great', 'excellent', 'happy', 'resolved', 'fixed', 'better', 'improved'],
            'negative': ['bad', 'terrible', 'awful', 'angry', 'frustrated', 'worse', 'broken', 'failed'],
            'urgent': ['emergency', 'urgent', 'immediately', 'asap', 'critical', 'dying', 'help']
        }
    
    def extract_entities(self, text):
        entities = {
            'locations': [],
            'dates': [],
            'numbers': [],
            'contacts': []
        }
        
        # Extract phone numbers
        phones = re.findall(r'\b\d{10}\b|\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b', text)
        entities['contacts'].extend(phones)
        
        # Extract numbers
        numbers = re.findall(r'\b\d+\b', text)
        entities['numbers'] = [int(n) for n in numbers if int(n) > 0]
        
        # Extract common location patterns
        location_patterns = ['in ', 'at ', 'near ', 'from ']
        for pattern in location_patterns:
            if pattern in text.lower():
                idx = text.lower().index(pattern)
                location = text[idx+len(pattern):idx+len(pattern)+30].split()[0]
                entities['locations'].append(location)
        
        return entities
    
    def sentiment_analysis(self, text):
        text_lower = text.lower()
        scores = {
            'positive': sum(1 for word in self.sentiment_words['positive'] if word in text_lower),
            'negative': sum(1 for word in self.sentiment_words['negative'] if word in text_lower),
            'urgent': sum(1 for word in self.sentiment_words['urgent'] if word in text_lower)
        }
        
        total = sum(scores.values())
        if total == 0:
            return {'sentiment': 'neutral', 'confidence': 0.5, 'scores': scores}
        
        dominant = max(scores, key=scores.get)
        confidence = scores[dominant] / total
        
        return {
            'sentiment': dominant,
            'confidence': round(confidence, 2),
            'scores': scores
        }
    
    def keyword_extraction(self, text, top_n=5):
        words = re.findall(r'\b\w{4,}\b', text.lower())
        stop_words = {'this', 'that', 'with', 'from', 'have', 'been', 'there', 'their', 'about'}
        words = [w for w in words if w not in stop_words]
        
        counter = Counter(words)
        return [word for word, count in counter.most_common(top_n)]
    
    def text_complexity(self, text):
        words = text.split()
        sentences = text.split('.')
        
        avg_word_length = sum(len(w) for w in words) / len(words) if words else 0
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        
        complexity = 'simple' if avg_word_length < 5 else 'moderate' if avg_word_length < 7 else 'complex'
        
        return {
            'complexity': complexity,
            'avg_word_length': round(avg_word_length, 1),
            'avg_sentence_length': round(avg_sentence_length, 1),
            'total_words': len(words)
        }

nlp_engine = AdvancedNLP()
