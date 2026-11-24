from app.analyzer import analyze_project

def test_secret_increases_risk_and_creates_security_finding():
    report = analyze_project([{"filename": "config.py", "content": 'api_key = "abcdefghijklmno"'}])
    assert report["overall_risk_level"] in {"medium", "high"}
    assert report["security_findings"] == 1
