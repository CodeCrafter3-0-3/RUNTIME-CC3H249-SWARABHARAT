import requests
import json
import sys

BASE_URL = "http://localhost:5000"
passed = 0
failed = 0

def test(name, method, endpoint, data=None, expect_status=200):
    global passed, failed
    try:
        url = f"{BASE_URL}{endpoint}"
        if method == "GET":
            r = requests.get(url, timeout=5)
        else:
            r = requests.post(url, json=data, timeout=5)
        
        if r.status_code == expect_status:
            print(f"✅ {name}")
            passed += 1
            return True
        else:
            print(f"❌ {name} - Expected {expect_status}, got {r.status_code}")
            failed += 1
            return False
    except Exception as e:
        print(f"❌ {name} - {str(e)[:50]}")
        failed += 1
        return False

print("=" * 60)
print("🔍 SWARABHARAT IMPLEMENTATION ALIGNMENT TEST")
print("=" * 60)

print("\n📌 CORE ENDPOINTS")
test("Health Check", "GET", "/health")
test("Home", "GET", "/")
test("Dashboard", "GET", "/dashboard")
test("Reports", "GET", "/reports")
test("Export CSV", "GET", "/export_csv")

print("\n📌 DEMO ENDPOINTS")
test("Demo Examples", "GET", "/demo_examples")
test("Demo Analyze", "POST", "/demo_analyze", {"message": "No water for 3 days"})
test("Demo Status", "GET", "/demo_status")
test("Demo Quota", "GET", "/demo_quota")

print("\n📌 ANALYTICS ENDPOINTS")
test("Trends", "GET", "/analytics/trends")
test("Insights", "GET", "/analytics/insights")
test("Priority", "GET", "/analytics/priority")
test("Stats", "GET", "/stats")

print("\n📌 AI/ML ENDPOINTS")
test("AI Insights", "GET", "/ai/insights")
test("AI Predictions", "GET", "/ai/predictions")
test("AI Anomalies", "GET", "/ai/anomalies")
test("AI Patterns", "GET", "/ai/patterns")
test("Index Status", "GET", "/ai/index_status")
test("Search Similar", "POST", "/ai/search_similar", {"text": "water problem", "top_n": 3})

print("\n📌 NEW FEATURES (JUST IMPLEMENTED)")
test("Heatmap", "GET", "/heatmap")
test("Hotspots", "GET", "/hotspots")
test("Hotspots with threshold", "GET", "/hotspots?threshold=3")
test("Translate", "POST", "/translate", {"text": "Hello", "target": "hi"})

print("\n📌 DEPARTMENT PORTAL")
test("Dept Login", "POST", "/department/login", {
    "username": "officer1",
    "password": "demo123",
    "department": "water"
})

print("\n📌 METRICS")
test("Metrics Text", "GET", "/metrics")
test("Metrics JSON", "GET", "/metrics_json")

print("\n" + "=" * 60)
print(f"✅ PASSED: {passed}")
print(f"❌ FAILED: {failed}")
print(f"📊 SUCCESS RATE: {round(passed/(passed+failed)*100, 1)}%")
print("=" * 60)

if failed == 0:
    print("\n🎉 ALL SYSTEMS ALIGNED AND WORKING!")
    sys.exit(0)
else:
    print(f"\n⚠️  {failed} endpoints need attention")
    sys.exit(1)
