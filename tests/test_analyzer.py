from app.analyzer import analyze_project

def test_secret_increases_risk_and_creates_security_finding():
    report = analyze_project([{"filename": "config.py", "content": 'api_key = "abcdefghijklmno"'}])
    assert report["overall_risk_level"] in {"medium", "high"}
    assert report["security_findings"] == 1
    assert report["files"][0]["prediction"]["bug_probability"] >= 60


def test_javascript_metrics_and_quality_findings_are_reported():
    content = """function calculate(items) {
  console.log(items);
  if (items.length) return items[0];
  return null;
}"""
    report = analyze_project([{"filename": "service.js", "content": content}])
    file_report = report["files"][0]
    assert file_report["language"] == "JavaScript"
    assert file_report["metrics"]["function_count"] == 1
    assert file_report["metrics"]["cyclomatic_complexity"] >= 2
    assert any(finding["message"] == "Debug console.log statement" for finding in file_report["findings"])


def test_project_summary_aggregates_multiple_files():
    report = analyze_project([{"filename": "a.py", "content": "def first():\n    return 1"}, {"filename": "b.ts", "content": "export const second = () => 2;"}])
    assert report["summary"]["files_analyzed"] == 2
    assert report["summary"]["total_lines_of_code"] == 3
