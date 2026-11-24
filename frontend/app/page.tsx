'use client';

import { useEffect, useState } from 'react';
import { AnalysisInsights } from './components/analysis-insights';

type Scan = { id: number; repository_name: string; overall_risk: string; risk_score: number; created_at: string };
type Report = { overall_risk_score: number; overall_risk_level: string; security_findings: number; summary: { files_analyzed: number; total_lines_of_code: number; average_complexity: number; quality_findings: number }; files: { filename: string; language: string; metrics: { lines_of_code: number; function_count: number; cyclomatic_complexity: number; duplicate_lines: number; todo_count: number }; prediction: { model: string; contributing_factors: string[] }; findings: Finding[] }[] };
type Finding = { severity: string; category: string; line: number; message: string };
type AuthResponse = { access_token: string; token_type: string; email: string; role: string };
type Session = Pick<AuthResponse, 'email' | 'role'>;

const api = process.env.NEXT_PUBLIC_API_URL || '';
const riskClass = (risk: string) => `risk-${risk || 'low'}`;

export default function Home() {
  const [token, setToken] = useState<string | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('developer@example.com');
  const [password, setPassword] = useState('ChangeMe123!');
  const [message, setMessage] = useState('');
  const [repo, setRepo] = useState('demo-repository');
  const [code, setCode] = useState('def calculate_total(items):\n    password = "super-secret-value"\n    total = 0\n    for item in items:\n        total += item["price"]\n    return total');
  const [report, setReport] = useState<Report | null>(null);
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(false);

  const request = async (path: string, init: RequestInit = {}) => {
    const response = await fetch(`${api}${path}`, { ...init, headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) } });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      const detail = Array.isArray(body.detail) ? body.detail[0]?.msg : body.detail;
      throw new Error(detail || 'Request failed. Please try again.');
    }
    return response.json();
  };

  const loadHistory = async () => { if (token) setScans(await request('/api/v1/scans')); };
  const loadSession = async () => { const current = await request('/api/v1/auth/me'); setSession(current); };

  useEffect(() => {
    const saved = localStorage.getItem('bugsentinelToken');
    if (saved) setToken(saved);
  }, []);

  useEffect(() => {
    if (!token) return;
    Promise.all([loadSession(), loadHistory()]).catch(() => { localStorage.removeItem('bugsentinelToken'); setToken(null); setSession(null); });
  }, [token]);

  const authenticate = async () => {
    setLoading(true); setMessage('');
    try {
      const path = mode === 'login' ? '/api/v1/auth/login' : '/api/v1/auth/register';
      const data: AuthResponse = await request(path, { method: 'POST', body: JSON.stringify({ email, password }) });
      localStorage.setItem('bugsentinelToken', data.access_token);
      setSession({ email: data.email, role: data.role });
      setToken(data.access_token);
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Authentication failed.'); }
    finally { setLoading(false); }
  };

  const continueWithGoogle = () => { window.location.assign(`${api}/api/v1/auth/google/login`); };

  const scan = async () => {
    setLoading(true); setMessage('');
    try {
      const data = await request('/api/v1/scans', { method: 'POST', body: JSON.stringify({ repository_name: repo, files: [{ filename: 'submitted_code.py', content: code }] }) });
      setReport(data); await loadHistory();
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Analysis unavailable.'); }
    finally { setLoading(false); }
  };

  const signOut = () => { localStorage.removeItem('bugsentinelToken'); setToken(null); setSession(null); setScans([]); setReport(null); };

  if (!token) return <main className="shell"><header className="topbar"><div className="brand"><b>B</b>BugSentinel <em>AI</em></div><div className="status">● Analysis engine online</div></header><section className="auth"><div><p className="eyebrow">DEVELOP WITH CONFIDENCE</p><h1>Find risky code<br />before it ships.</h1><p className="muted">BugSentinel combines code metrics and security checks into one clear report.</p><div className="chips"><span>Bug-risk scoring</span><span>Security signals</span><span>Actionable findings</span></div></div><div className="panel login"><p className="eyebrow">SECURE ACCESS</p><h2>{mode === 'login' ? 'Welcome back' : 'Create your workspace'}</h2><p className="muted">{mode === 'login' ? 'Sign in to start an analysis.' : 'Create a developer account to securely save scan history.'}</p><button className="google-button" onClick={continueWithGoogle}><b>G</b> Continue with Google <span>↗</span></button><div className="auth-divider"><span>or use email</span></div><label htmlFor="email">Email address</label><input id="email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} /><label htmlFor="password">Password</label><input id="password" type="password" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} value={password} onChange={(event) => setPassword(event.target.value)} />{mode === 'register' && <small className="password-help">Use 12+ characters with uppercase, lowercase, and a number.</small>}<button onClick={authenticate} disabled={loading}>{loading ? 'Please wait…' : mode === 'login' ? 'Enter workspace' : 'Create account'} <span>↗</span></button>{message && <p className="error" role="alert">{message}</p>}<button className="switch-mode" onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setMessage(''); }}>{mode === 'login' ? 'New here? Create an account' : 'Already have an account? Sign in'}</button>{mode === 'login' && <small>Demo access is prefilled for this prototype.</small>}</div></section></main>;

  const findings = report?.files.flatMap((file) => file.findings.map((finding) => ({ ...finding, filename: file.filename }))) || [];
  return <main className="shell"><header className="topbar"><div className="brand"><b>B</b>BugSentinel <em>AI</em></div><div className="status">● Analysis engine online</div></header><section className="intro"><div><p className="eyebrow">YOUR WORKSPACE</p><h1>Code intelligence, <i>simplified.</i></h1><p className="muted">Submit a file, inspect its risk signals, and track every scan.</p></div><div className="session"><span>{session?.email}</span><button className="link" onClick={signOut}>Sign out</button></div></section><section className="metrics"><article><small>ANALYSIS STATUS</small><strong className="good">● Ready</strong><p>Engine healthy</p></article><article><small>ACCESS LEVEL</small><strong>{session?.role || 'Developer'}</strong><p>JWT protected session</p></article><article><small>API ACCESS</small><a href="/docs" target="_blank">Open Swagger ↗</a><p>Explore REST endpoints</p></article></section><section className="workspace"><article className="panel scan"><div className="heading"><div><p className="eyebrow">NEW ANALYSIS</p><h2>Review source code</h2></div><span>1 FILE</span></div><label htmlFor="repository">Repository / project name</label><input id="repository" value={repo} onChange={(event) => setRepo(event.target.value)} /><label htmlFor="source">Source code</label><textarea id="source" value={code} onChange={(event) => setCode(event.target.value)} /><button onClick={scan} disabled={loading}>{loading ? 'Analyzing…' : 'Run analysis'} <span>↗</span></button>{message && <p className="error" role="alert">{message}</p>}</article><aside className="panel result"><div className="heading"><div><p className="eyebrow">LATEST RESULT</p><h2>Risk report</h2></div>{report && <span className={riskClass(report.overall_risk_level)}>{report.overall_risk_level} RISK</span>}</div>{!report ? <div className="empty"><div>◉</div><h3>No analysis yet</h3><p>Submit source code to generate a bug-risk and security report.</p></div> : <><div className={`score ${riskClass(report.overall_risk_level)}`}><div><small>OVERALL RISK SCORE</small><strong>{report.overall_risk_score}<i>/100</i></strong></div><b>{report.overall_risk_level}</b></div><p className="summary">{report.files.length} file analyzed <span>{report.security_findings} security signals</span></p><AnalysisInsights report={report} />{findings.length ? findings.slice(0, 5).map((finding) => <article className="finding" key={`${finding.line}-${finding.message}`}><span className={riskClass(finding.severity)}>{finding.severity}</span><div><strong>{finding.message}</strong><small>{finding.filename} · line {finding.line}</small></div></article>) : <p className="good">No rule-based issues found.</p>}</>}</aside></section><section className="panel history"><div className="heading"><div><p className="eyebrow">SCAN HISTORY</p><h2>Recent analyses</h2></div><button className="link" onClick={loadHistory}>Refresh</button></div>{scans.length ? scans.map((item) => <article className="scanrow" key={item.id}><span className="scanicon">⌁</span><div><strong>{item.repository_name}</strong><small>{new Date(item.created_at).toLocaleString()}</small></div><b className={riskClass(item.overall_risk)}>{item.risk_score}<i>/100</i></b><span className={riskClass(item.overall_risk)}>{item.overall_risk}</span></article>) : <p className="emptytext">Your completed scans will appear here.</p>}</section></main>;
}
