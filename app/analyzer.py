"""Explainable heuristic bug-risk analysis used until a trained model is introduced."""
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Finding:
    severity: str
    category: str
    line: int
    message: str


LANGUAGES = {".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript", ".java": "Java"}
SECRET_PATTERNS = [(r"(?i)(api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"]{8,}['\"]", "Possible hard-coded secret"), (r"AKIA[0-9A-Z]{16}", "Possible AWS access key")]
UNSAFE_PATTERNS = [(r"\beval\s*\(", "Use of eval can enable code injection"), (r"\bexec\s*\(", "Use of exec can enable code injection"), (r"SELECT .+\+", "Possible SQL string concatenation")]
COMPLEXITY_PATTERN = re.compile(r"\b(if|for|while|case|catch|elif|except|switch|when|and|or|&&|\|\|)\b")


def _language(filename: str) -> str:
    return LANGUAGES.get(Path(filename).suffix.lower(), "Text")


def _function_count(lines: list[str], language: str) -> int:
    if language == "Python":
        return sum(bool(re.match(r"\s*(async\s+)?def\s+\w+", line)) for line in lines)
    if language in {"JavaScript", "TypeScript"}:
        return sum(bool(re.search(r"\bfunction\s+\w+|\b\w+\s*=\s*(async\s*)?\([^)]*\)\s*=>", line)) for line in lines)
    if language == "Java":
        return sum(bool(re.match(r"\s*(public|private|protected)?\s*(static\s+)?\w+[<>\w, ]*\s+\w+\s*\([^;]*\)\s*\{", line)) for line in lines)
    return 0


def analyze_file(filename: str, content: str) -> dict:
    lines = content.splitlines()
    language = _language(filename)
    findings: list[Finding] = []
    complexity, long_lines, todos, comments, max_nesting = 1, 0, 0, 0, 0
    normalized_lines: list[str] = []

    for number, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("/*"):
            comments += 1
        if stripped:
            normalized_lines.append(re.sub(r"\s+", " ", stripped))
        max_nesting = max(max_nesting, len(line) - len(line.lstrip()))
        if len(line) > 120:
            long_lines += 1
            findings.append(Finding("low", "quality", number, "Line exceeds 120 characters"))
        if "TODO" in line.upper():
            todos += 1
            findings.append(Finding("low", "quality", number, "Unresolved TODO marker"))
        complexity += len(COMPLEXITY_PATTERN.findall(line))
        for expression, message in SECRET_PATTERNS:
            if re.search(expression, line):
                findings.append(Finding("high", "security", number, message))
        for expression, message in UNSAFE_PATTERNS:
            if re.search(expression, line, re.IGNORECASE):
                findings.append(Finding("medium", "security", number, message))
        if language in {"JavaScript", "TypeScript"} and re.search(r"\bconsole\.log\s*\(", line):
            findings.append(Finding("low", "quality", number, "Debug console.log statement"))
        if language == "Python" and re.match(r"\s*except\s*:", line):
            findings.append(Finding("medium", "quality", number, "Bare except can hide unexpected errors"))
        if re.search(r"catch\s*\([^)]*\)\s*\{\s*\}", line):
            findings.append(Finding("medium", "quality", number, "Empty catch block suppresses errors"))

    duplicate_lines = sum(count - 1 for count in Counter(normalized_lines).values() if count > 1)
    if duplicate_lines >= 3:
        findings.append(Finding("medium", "quality", 0, f"{duplicate_lines} repeated code lines detected"))

    factors: list[str] = []
    if complexity >= 12:
        factors.append(f"High branching complexity ({complexity})")
    if len(lines) >= 200:
        factors.append(f"Large file ({len(lines)} lines)")
    if duplicate_lines >= 3:
        factors.append(f"Repeated code ({duplicate_lines} lines)")
    if todos:
        factors.append(f"Unresolved TODOs ({todos})")
    if any(finding.severity == "high" for finding in findings):
        factors.append("High-severity security finding")
    if not factors:
        factors.append("No high-impact heuristic risk factors found")

    score = complexity * 3 + len(lines) // 8 + long_lines * 2 + todos * 3 + duplicate_lines * 2
    score += sum(25 if finding.severity == "high" else 12 if finding.severity == "medium" else 2 for finding in findings)
    if any(finding.severity == "high" and finding.category == "security" for finding in findings):
        score = max(score, 60)
    score = min(100, score)
    risk_level = "high" if score >= 60 else "medium" if score >= 30 else "low"
    return {
        "filename": filename,
        "language": language,
        "metrics": {"lines_of_code": len(lines), "comment_lines": comments, "function_count": _function_count(lines, language), "cyclomatic_complexity": complexity, "long_lines": long_lines, "todo_count": todos, "duplicate_lines": duplicate_lines, "max_indentation": max_nesting},
        "prediction": {"model": "BugSentinel heuristic v1", "bug_probability": score, "contributing_factors": factors},
        "risk_score": score,
        "risk_level": risk_level,
        "findings": [asdict(finding) for finding in findings],
    }


def analyze_project(files: list[dict]) -> dict:
    reports = [analyze_file(item["filename"], item["content"]) for item in files]
    score = round(sum(item["risk_score"] for item in reports) / len(reports)) if reports else 0
    security_findings = sum(sum(finding["category"] == "security" for finding in item["findings"]) for item in reports)
    quality_findings = sum(sum(finding["category"] == "quality" for finding in item["findings"]) for item in reports)
    return {"overall_risk_score": score, "overall_risk_level": "high" if score >= 60 else "medium" if score >= 30 else "low", "summary": {"files_analyzed": len(reports), "total_lines_of_code": sum(item["metrics"]["lines_of_code"] for item in reports), "average_complexity": round(sum(item["metrics"]["cyclomatic_complexity"] for item in reports) / len(reports), 1) if reports else 0, "security_findings": security_findings, "quality_findings": quality_findings}, "security_findings": security_findings, "files": reports}
