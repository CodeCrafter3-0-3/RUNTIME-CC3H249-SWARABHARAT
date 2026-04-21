import json
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def load_training_data():
    reports = []
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

def train_urgency_predictor():
    reports = load_training_data()
    
    if len(reports) < 50:
        print(f"Need at least 50 reports. Found: {len(reports)}")
        print("Run: python generate_training_data.py")
        return
    
    X = [r.get('message', '') for r in reports]
    y = [1 if r.get('urgency') == 'High' else 0 for r in reports]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    vectorizer = TfidfVectorizer(max_features=300)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    clf = LogisticRegression(max_iter=1000, random_state=42)
    clf.fit(X_train_vec, y_train)
    
    y_pred = clf.predict(X_test_vec)
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    
    print(f"\nAccuracy: {accuracy:.2%}")
    print(f"F1 Score: {f1:.2%}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Low/Medium', 'High']))
    
    os.makedirs('../models', exist_ok=True)
    with open('../models/urgency_predictor.pkl', 'wb') as f:
        pickle.dump({'vectorizer': vectorizer, 'classifier': clf, 'accuracy': accuracy, 'f1': f1}, f)
    
    print(f"\nModel saved with {accuracy:.2%} accuracy")
    return accuracy

if __name__ == '__main__':
    train_urgency_predictor()
