import json
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def load_training_data():
    reports = []
    
    # Try loading from multiple sources
    files = ['../data/reports.json', 'synthetic_reports.json']
    
    for file in files:
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        reports.append(json.loads(line.strip()))
                    except:
                        pass
    
    return reports

def train_issue_classifier():
    reports = load_training_data()
    
    if len(reports) < 50:
        print(f"Need at least 50 reports. Found: {len(reports)}")
        print("Run: python generate_training_data.py")
        return
    
    X = [r.get('message', '') for r in reports]
    y = [r.get('issue', 'Other') for r in reports]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    vectorizer = TfidfVectorizer(max_features=500, ngram_range=(1, 2))
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train_vec, y_train)
    
    y_pred = clf.predict(X_test_vec)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\nAccuracy: {accuracy:.2%}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    os.makedirs('../models', exist_ok=True)
    with open('../models/issue_classifier.pkl', 'wb') as f:
        pickle.dump({'vectorizer': vectorizer, 'classifier': clf, 'accuracy': accuracy}, f)
    
    print(f"\nModel saved with {accuracy:.2%} accuracy")
    return accuracy

if __name__ == '__main__':
    train_issue_classifier()
