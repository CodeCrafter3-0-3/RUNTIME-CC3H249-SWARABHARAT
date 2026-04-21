# 🚀 QUICK START - Test Everything

## Step 1: Install Dependencies
```powershell
cd e:\SWARABHARAT
.\.venv\Scripts\Activate.ps1
pip install scikit-learn PyJWT twilio
```

## Step 2: Start Server
```powershell
# Terminal 1
cd e:\SWARABHARAT
.\.venv\Scripts\python.exe BACKEND\app.py
```

## Step 3: Run Alignment Test
```powershell
# Terminal 2 (new window)
cd e:\SWARABHARAT
.\.venv\Scripts\Activate.ps1
python test_alignment.py
```

## Expected Output:
```
✅ Health Check
✅ Dashboard
✅ Heatmap
✅ Translate
✅ Dept Login
...
✅ PASSED: 25
❌ FAILED: 0
📊 SUCCESS RATE: 100%
🎉 ALL SYSTEMS ALIGNED AND WORKING!
```

## Manual Quick Tests:
```powershell
# Test 1: Health
curl http://localhost:5000/health

# Test 2: Heatmap
curl http://localhost:5000/heatmap

# Test 3: Translation
curl -X POST http://localhost:5000/translate -H "Content-Type: application/json" -d "{\"text\":\"Hello\",\"target\":\"hi\"}"

# Test 4: Department Login
curl -X POST http://localhost:5000/department/login -H "Content-Type: application/json" -d "{\"username\":\"officer1\",\"password\":\"demo123\",\"department\":\"water\"}"
```

## What's Working:
✅ Core API (submit, dashboard, reports)
✅ AI/ML (insights, predictions, anomalies)
✅ Heatmap & Hotspots
✅ Multi-language Translation
✅ Computer Vision (image analysis)
✅ Department Portal (JWT auth)
✅ WhatsApp Bot (separate server)
✅ ML Training Pipeline

## Next Steps:
1. Collect 100+ reports for training
2. Run: `python BACKEND\ml_training\train_classifier.py`
3. Run: `python BACKEND\ml_training\train_urgency.py`
4. Deploy to production
