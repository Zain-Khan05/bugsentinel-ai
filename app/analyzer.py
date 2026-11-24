import re
from dataclasses import asdict, dataclass

@dataclass
class Finding:
    severity: str
    category: str
    line: int
    message: str

SECRET_PATTERNS = [(r"(?i)(api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"]{8,}['\"]", "Possible hard-coded secret"), (r"AKIA[0-9A-Z]{16}", "Possible AWS access key")]
UNSAFE_PATTERNS = [(r"\beval\s*\(", "Use of eval can enable code injection"), (r"\bexec\s*\(", "Use of exec can enable code injection"), (r"SELECT .+\+", "Possible SQL string concatenation")]

def analyze_file(filename: str, content: str) -> dict:
    lines, findings, complexity, long_lines, todos = content.splitlines(), [], 1, 0, 0
    for number, line in enumerate(lines, 1):
        if len(line) > 120:
            long_lines += 1; findings.append(Finding("low", "quality", number, "Line exceeds 120 characters"))
        todos += int("TODO" in line.upper())
        complexity += len(re.findall(r"\b(if|for|while|case|catch|elif|and|or)\b", line))
        for expression, message in SECRET_PATTERNS:
            if re.search(expression, line): findings.append(Finding("high", "security", number, message))
        for expression, message in UNSAFE_PATTERNS:
            if re.search(expression, line, re.I): findings.append(Finding("medium", "security", number, message))
    score = complexity * 3 + len(lines) // 8 + long_lines * 2 + todos * 3 + sum(25 if f.severity == "high" else 12 if f.severity == "medium" else 2 for f in findings)
    if any(finding.severity == "high" and finding.category == "security" for finding in findings):
        score = max(score, 60)
    score = min(100, score)
    return {"filename": filename, "metrics": {"lines_of_code": len(lines), "cyclomatic_complexity": complexity, "long_lines": long_lines, "todo_count": todos}, "risk_score": score, "risk_level": "high" if score >= 60 else "medium" if score >= 30 else "low", "findings": [asdict(f) for f in findings]}

def analyze_project(files: list[dict]) -> dict:
    reports = [analyze_file(item["filename"], item["content"]) for item in files]
    score = round(sum(item["risk_score"] for item in reports) / len(reports)) if reports else 0
    return {"overall_risk_score": score, "overall_risk_level": "high" if score >= 60 else "medium" if score >= 30 else "low", "security_findings": sum(sum(f["category"] == "security" for f in item["findings"]) for item in reports), "files": reports}
