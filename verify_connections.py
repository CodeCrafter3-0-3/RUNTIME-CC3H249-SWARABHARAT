import sys
import os

print("=" * 60)
print("SWARABHARAT CONNECTION VERIFICATION")
print("=" * 60)

errors = []
warnings = []
success = []

# 1. Check Backend Imports
print("\n1. Checking Backend Module Connections...")
try:
    sys.path.insert(0, 'BACKEND')
    
    from ai_engine import analyze_issue
    success.append("ai_engine.py connected")
    
    from data_handler import save_report, read_reports
    success.append("data_handler.py connected")
    
    from ml_engine import calculate_priority_score
    success.append("ml_engine.py connected")
    
    from nlp_engine import nlp_engine
    success.append("nlp_engine.py connected")
    
    from forecasting_engine import forecaster
    success.append("forecasting_engine.py connected")
    
    from clustering_engine import clustering_engine
    success.append("clustering_engine.py connected")
    
    from security import hash_password, sanitize_input
    success.append("security.py connected")
    
    from translation import translate_text
    success.append("translation.py connected")
    
    from heatmap_generator import generate_heatmap_data
    success.append("heatmap_generator.py connected")
    
except Exception as e:
    errors.append(f"Backend import error: {str(e)}")

# 2. Check ML Models
print("\n2. Checking ML Models...")
models_dir = "BACKEND/models"
if os.path.exists(models_dir):
    models = os.listdir(models_dir)
    if 'issue_classifier.pkl' in models:
        success.append("Issue classifier model exists")
    else:
        warnings.append("Issue classifier model missing")
    
    if 'urgency_predictor.pkl' in models:
        success.append("Urgency predictor model exists")
    else:
        warnings.append("Urgency predictor model missing")
else:
    errors.append("Models directory not found")

# 3. Check Training Data
print("\n3. Checking Training Data...")
if os.path.exists("BACKEND/synthetic_reports.json"):
    success.append("Training data exists")
else:
    warnings.append("Training data missing - run generate_training_data.py")

# 4. Check Frontend Files
print("\n4. Checking Frontend Files...")
frontend_files = [
    "FRONTEND/index.html",
    "FRONTEND/ai-insights.html",
    "FRONTEND/admin/admin.html",
    "FRONTEND/css/glassmorphism.css"
]

for file in frontend_files:
    if os.path.exists(file):
        success.append(f"{file} exists")
    else:
        errors.append(f"{file} missing")

# 5. Check API Endpoints
print("\n5. Checking API Endpoint Definitions...")
try:
    with open("BACKEND/app.py", 'r', encoding='utf-8') as f:
        app_content = f.read()
        
    endpoints = [
        '/submit', '/dashboard', '/reports', '/heatmap',
        '/ml/nlp_analysis', '/ml/forecast', '/ml/clusters',
        '/ai/insights', '/ai/predictions', '/translate'
    ]
    
    for endpoint in endpoints:
        if f"@app.route('{endpoint}" in app_content or f'@app.route("{endpoint}' in app_content:
            success.append(f"Endpoint {endpoint} defined")
        else:
            warnings.append(f"Endpoint {endpoint} not found")
            
except Exception as e:
    errors.append(f"Could not verify endpoints: {str(e)}")

# 6. Check Database Handler
print("\n6. Checking Database Integration...")
try:
    from db_handler import save_report_db, read_reports_db
    success.append("Database handler connected")
except Exception as e:
    warnings.append(f"Database handler issue: {str(e)}")

# 7. Check Dependencies
print("\n7. Checking Dependencies...")
try:
    import flask
    success.append("Flask installed")
except:
    errors.append("Flask not installed")

try:
    import sklearn
    success.append("scikit-learn installed")
except:
    warnings.append("scikit-learn not installed")

try:
    import bcrypt
    success.append("bcrypt installed")
except:
    warnings.append("bcrypt not installed")

# Print Results
print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)

print(f"\nSUCCESS ({len(success)}):")
for s in success[:10]:
    print(f"  - {s}")
if len(success) > 10:
    print(f"  ... and {len(success) - 10} more")

if warnings:
    print(f"\nWARNINGS ({len(warnings)}):")
    for w in warnings:
        print(f"  - {w}")

if errors:
    print(f"\nERRORS ({len(errors)}):")
    for e in errors:
        print(f"  - {e}")
else:
    print("\nERRORS: None")

# Overall Status
print("\n" + "=" * 60)
if not errors and len(warnings) <= 2:
    print("STATUS: ALL SYSTEMS CONNECTED")
elif not errors:
    print("STATUS: MOSTLY CONNECTED (minor warnings)")
else:
    print("STATUS: CONNECTION ISSUES FOUND")
print("=" * 60)
