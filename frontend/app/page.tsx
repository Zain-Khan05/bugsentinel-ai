'use client';

import { useEffect, useState } from 'react';
import { AnalysisInsights } from './components/analysis-insights';

type Scan = { id: number; repository_name: string; overall_risk: string; risk_score: number; created_at: string };
type Report = { overall_risk_score: number; overall_risk_level: string; security_findings: number; summary: { files_analyzed: number; total_lines_of_code: number; average_complexity: number; quality_findings: number }; files: { filename: string; language: string; risk_score: number; risk_level: string; metrics: { lines_of_code: number; function_count: number; cyclomatic_complexity: number; duplicate_lines: number; todo_count: number }; prediction: { model: string; contributing_factors: string[] }; findings: Finding[] }[] };
type Finding = { severity: string; category: string; line: number; message: string };
type AuthResponse = { access_token: string; token_type: string; email: string; role: string };
type Session = Pick<AuthResponse, 'email' | 'role'>;
type SourceFilePayload = { filename: string; content: string };
type SavedScanDetail = Report & { repository_name: string; source_files: SourceFilePayload[] };

const api = process.env.NEXT_PUBLIC_API_URL || '';
const riskClass = (risk: string) => `risk-${risk || 'low'}`;
const supportedExtensions = ['.py', '.js', '.jsx', '.ts', '.tsx', '.java'];
const acceptedSourceFiles = supportedExtensions.join(',');

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
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [passwordMessage, setPasswordMessage] = useState('');
  const [downloadingReport, setDownloadingReport] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<SourceFilePayload[]>([]);

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

  const changePassword = async () => {
    setLoading(true); setPasswordMessage('');
    try {
      const data = await request('/api/v1/auth/change-password', { method: 'POST', body: JSON.stringify({ current_password: currentPassword, password: newPassword }) });
      setPasswordMessage(data.message); setCurrentPassword(''); setNewPassword(''); setShowPasswordForm(false);
    } catch (error) { setPasswordMessage(error instanceof Error ? error.message : 'Unable to change password.'); }
    finally { setLoading(false); }
  };

  const scan = async () => {
    setLoading(true); setMessage('');
    try {
      const files = [
        ...(code.trim() ? [{ filename: 'submitted_code.py', content: code }] : []),
        ...uploadedFiles,
      ];
      if (files.length === 0) throw new Error('Paste source code or choose at least one supported source file.');
      const data = await request('/api/v1/scans', { method: 'POST', body: JSON.stringify({ repository_name: repo, files }) });
      setReport(data); await loadHistory();
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Analysis unavailable.'); }
    finally { setLoading(false); }
  };

  const addFiles = async (files: FileList | null) => {
    if (!files) return;
    setMessage('');
    const selections = Array.from(files);
    const unsupported = selections.filter((file) => !supportedExtensions.some((extension) => file.name.toLowerCase().endsWith(extension)));
    if (unsupported.length) {
      setMessage(`Unsupported file type: ${unsupported.map((file) => file.name).join(', ')}. Choose only ${acceptedSourceFiles}.`);
      return;
    }
    if (selections.some((file) => file.size > 200_000)) {
      setMessage('Each source file must be 200 KB or smaller.');
      return;
    }
    if (uploadedFiles.length + selections.length + (code.trim() ? 1 : 0) > 25) {
      setMessage('A scan can contain a maximum of 25 source files.');
      return;
    }
    const newFiles = await Promise.all(selections.map(async (file) => ({ filename: file.name, content: await file.text() })));
    setUploadedFiles((current) => [...current, ...newFiles]);
  };

  const openSavedScan = async (scanId: number) => {
    setLoading(true); setMessage('');
    try {
      const savedScan = await request(`/api/v1/scans/${scanId}`) as SavedScanDetail;
      const pastedSource = savedScan.source_files.find((file) => file.filename === 'submitted_code.py');
      setRepo(savedScan.repository_name);
      setCode(pastedSource?.content || '');
      setUploadedFiles(savedScan.source_files.filter((file) => file.filename !== 'submitted_code.py'));
      setReport(savedScan);
      setMessage(savedScan.source_files.length ? `Restored ${savedScan.source_files.length} saved source file${savedScan.source_files.length === 1 ? '' : 's'}.` : 'This older scan has its saved report, but source files were not stored at the time it was created.');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Unable to open the saved analysis.'); }
    finally { setLoading(false); }
  };

  const downloadReport = async () => {
    if (!report) return;
    setDownloadingReport(true);
    try {
      const { jsPDF } = await import('jspdf');
      const pdf = new jsPDF({ unit: 'mm', format: 'a4' });
      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      const margin = 16;
      let y = 18;
      const addPageIfNeeded = (height = 8) => {
        if (y + height <= pageHeight - 16) return;
        pdf.addPage();
        y = 18;
      };
      const write = (text: string, size = 10, color: [number, number, number] = [35, 50, 83]) => {
        pdf.setFontSize(size);
        pdf.setTextColor(...color);
        const lines = pdf.splitTextToSize(text, pageWidth - margin * 2) as string[];
        addPageIfNeeded(lines.length * (size * 0.45) + 3);
        pdf.text(lines, margin, y);
        y += lines.length * (size * 0.45) + 3;
      };
      const heading = (text: string) => {
        addPageIfNeeded(12);
        y += 3;
        pdf.setDrawColor(137, 157, 255);
        pdf.line(margin, y, pageWidth - margin, y);
        y += 6;
        write(text, 13, [59, 78, 141]);
      };

      pdf.setFillColor(14, 25, 51);
      pdf.rect(0, 0, pageWidth, 42, 'F');
      pdf.setTextColor(238, 243, 252);
      pdf.setFontSize(21);
      pdf.text('BugSentinel AI', margin, 19);
      pdf.setFontSize(10);
      pdf.text('Code Analysis & Bug-Risk Report', margin, 27);
      pdf.setTextColor(170, 185, 255);
      pdf.text(`Generated ${new Date().toLocaleString()}`, margin, 34);
      y = 52;

      write(`Repository / project: ${repo}`, 11);
      write(`Overall risk: ${report.overall_risk_level.toUpperCase()} (${report.overall_risk_score}/100)`, 11, report.overall_risk_level === 'high' ? [177, 44, 69] : report.overall_risk_level === 'medium' ? [166, 108, 17] : [24, 117, 79]);

      heading('Analysis summary');
      write(`Files analyzed: ${report.summary.files_analyzed}  |  Lines of code: ${report.summary.total_lines_of_code}  |  Average complexity: ${report.summary.average_complexity}`);
      write(`Security findings: ${report.security_findings}  |  Quality findings: ${report.summary.quality_findings}`);

      report.files.forEach((file, index) => {
        heading(`File ${index + 1}: ${file.filename}`);
        write(`Language: ${file.language}`);
        write(`Risk: ${file.risk_level.toUpperCase()} (${file.risk_score}/100)  |  LOC: ${file.metrics.lines_of_code}  |  Functions: ${file.metrics.function_count}  |  Complexity: ${file.metrics.cyclomatic_complexity}`);
        write(`Prediction model: ${file.prediction.model}`);
        write(`Contributing factors: ${file.prediction.contributing_factors.join('; ')}`);

        heading('Findings');
        if (file.findings.length === 0) {
          write('No security or quality findings were detected.', 10, [24, 117, 79]);
        } else {
          file.findings.forEach((finding) => write(`[${finding.severity.toUpperCase()}] ${finding.category} — line ${finding.line || 'N/A'}: ${finding.message}`));
        }
      });

      const safeName = repo.trim().replace(/[^a-z0-9_-]+/gi, '-').replace(/^-|-$/g, '') || 'analysis';
      pdf.save(`bugsentinel-${safeName}-report.pdf`);
    } finally {
      setDownloadingReport(false);
    }
  };

  const signOut = () => { localStorage.removeItem('bugsentinelToken'); setToken(null); setSession(null); setScans([]); setReport(null); };

  if (!token) {
    const isLogin = mode === 'login';
    const title = isLogin ? 'Welcome back' : 'Create your workspace';
    const subtitle = isLogin ? 'Sign in to start an analysis.' : 'Create a developer account to securely save scan history.';
    const switchMode = (nextMode: 'login' | 'register') => {
      setMode(nextMode); setEmail(nextMode === 'login' ? 'developer@example.com' : ''); setPassword(nextMode === 'login' ? 'ChangeMe123!' : ''); setMessage('');
    };
    return <main className="shell"><header className="topbar"><div className="brand"><b>B</b>BugSentinel <em>AI</em></div><div className="status">● Analysis engine online</div></header><section className="auth"><div><p className="eyebrow">DEVELOP WITH CONFIDENCE</p><h1>Find risky code<br />before it ships.</h1><p className="muted">BugSentinel combines code metrics and security checks into one clear report.</p><div className="chips"><span>Bug-risk scoring</span><span>Security signals</span><span>Actionable findings</span></div></div><div className="panel login"><p className="eyebrow">SECURE ACCESS</p><h2>{title}</h2><p className="muted">{subtitle}</p><button className="google-button" onClick={continueWithGoogle}><b>G</b> Continue with Google <span>↗</span></button><div className="auth-divider"><span>or use email</span></div><label htmlFor="email">Email address</label><input id="email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} /><label htmlFor="password">Password</label><input id="password" type="password" autoComplete={isLogin ? 'current-password' : 'new-password'} value={password} onChange={(event) => setPassword(event.target.value)} />{!isLogin && <small className="password-help">Use 12+ characters with uppercase, lowercase, and a number.</small>}<button onClick={authenticate} disabled={loading}>{loading ? 'Please wait…' : isLogin ? 'Enter workspace' : 'Create account'} <span>↗</span></button>{message && <p className="error" role="alert">{message}</p>}{isLogin ? <><button className="switch-mode" onClick={() => switchMode('register')}>New here? Create an account</button><small>Demo access is prefilled for this prototype.</small></> : <button className="switch-mode" onClick={() => switchMode('login')}>Already have an account? Sign in</button>}</div></section></main>;
  }

  const findings = report?.files.flatMap((file) => file.findings.map((finding) => ({ ...finding, filename: file.filename }))) || [];
  return <main className="shell"><header className="topbar"><div className="brand"><b>B</b>BugSentinel <em>AI</em></div><div className="status">● Analysis engine online</div></header><section className="intro"><div><p className="eyebrow">YOUR WORKSPACE</p><h1>Code intelligence, <i>simplified.</i></h1><p className="muted">Submit a file, inspect its risk signals, and track every scan.</p></div><div className="session"><span>{session?.email}</span><button className="link" onClick={() => { setShowPasswordForm(!showPasswordForm); setPasswordMessage(''); }}>Change password</button><button className="link" onClick={signOut}>Sign out</button></div></section>{showPasswordForm && <section className="panel account-security"><div className="heading"><div><p className="eyebrow">ACCOUNT SECURITY</p><h2>Change password</h2></div><button className="link" onClick={() => setShowPasswordForm(false)}>Close</button></div><p className="muted">Confirm your current password before choosing a new one.</p><div className="password-fields"><div><label htmlFor="current-password">Current password</label><input id="current-password" type="password" autoComplete="current-password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} /></div><div><label htmlFor="new-password">New password</label><input id="new-password" type="password" autoComplete="new-password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} /></div></div><small className="password-help">Use 12+ characters with uppercase, lowercase, and a number.</small><button className="password-submit" onClick={changePassword} disabled={loading}>{loading ? 'Updating…' : 'Update password'}</button>{passwordMessage && <p className={passwordMessage.includes('successfully') ? 'success' : 'error'} role="alert">{passwordMessage}</p>}</section>}<section className="metrics"><article><small>ANALYSIS STATUS</small><strong className="good">● Ready</strong><p>Engine healthy</p></article><article><small>ACCESS LEVEL</small><strong>{session?.role || 'Developer'}</strong><p>JWT protected session</p></article><article><small>API ACCESS</small><a href="/docs" target="_blank">Open Swagger ↗</a><p>Explore REST endpoints</p></article></section><section className="workspace"><article className="panel scan"><div className="heading"><div><p className="eyebrow">NEW ANALYSIS</p><h2>Review source code</h2></div><span>{uploadedFiles.length + (code.trim() ? 1 : 0)} FILES</span></div><label htmlFor="repository">Repository / project name</label><input id="repository" value={repo} onChange={(event) => setRepo(event.target.value)} /><label htmlFor="source">Paste source code <small>(optional)</small></label><textarea id="source" value={code} onChange={(event) => setCode(event.target.value)} /><label className="file-picker" htmlFor="source-files"><span>Choose supported source files</span><small>{acceptedSourceFiles} · Maximum 25 files</small><input id="source-files" type="file" accept={acceptedSourceFiles} multiple onChange={async (event) => { await addFiles(event.target.files); event.currentTarget.value = ''; }} /></label>{uploadedFiles.length > 0 && <div className="selected-files">{uploadedFiles.map((file, index) => <span key={`${file.filename}-${index}`}>{file.filename}<button type="button" aria-label={`Remove ${file.filename}`} onClick={() => setUploadedFiles((current) => current.filter((_, currentIndex) => currentIndex !== index))}>×</button></span>)}</div>}<button onClick={scan} disabled={loading}>{loading ? 'Analyzing…' : 'Run analysis'} <span>↗</span></button>{message && <p className="error" role="alert">{message}</p>}</article><aside className="panel result"><div className="heading"><div><p className="eyebrow">LATEST RESULT</p><h2>Risk report</h2></div>{report && <span className={riskClass(report.overall_risk_level)}>{report.overall_risk_level} RISK</span>}</div>{!report ? <div className="empty"><div>◉</div><h3>No analysis yet</h3><p>Submit source code to generate a bug-risk and security report.</p></div> : <><div className={`score ${riskClass(report.overall_risk_level)}`}><div><small>OVERALL RISK SCORE</small><strong>{report.overall_risk_score}<i>/100</i></strong></div><b>{report.overall_risk_level}</b></div><p className="summary">{report.files.length} file analyzed <span>{report.security_findings} security signals</span></p><AnalysisInsights report={report} /><button className="download-report" onClick={downloadReport} disabled={downloadingReport}>{downloadingReport ? 'Preparing PDF…' : 'Download PDF report'}</button>{findings.length ? findings.slice(0, 5).map((finding) => <article className="finding" key={`${finding.line}-${finding.message}`}><span className={riskClass(finding.severity)}>{finding.severity}</span><div><strong>{finding.message}</strong><small>{finding.filename} · line {finding.line}</small></div></article>) : <p className="good">No rule-based issues found.</p>}</>}</aside></section><section className="panel history"><div className="heading"><div><p className="eyebrow">SCAN HISTORY</p><h2>Recent analyses</h2></div><button className="link" onClick={loadHistory}>Refresh</button></div>{scans.length ? scans.map((item) => <article className="scanrow" key={item.id}><span className="scanicon">⌁</span><div><strong>{item.repository_name}</strong><small>{new Date(item.created_at).toLocaleString()}</small></div><b className={riskClass(item.overall_risk)}>{item.risk_score}<i>/100</i></b><span className={riskClass(item.overall_risk)}>{item.overall_risk}</span><button className="open-scan" onClick={() => openSavedScan(item.id)} disabled={loading}>Open</button></article>) : <p className="emptytext">Your completed scans will appear here.</p>}</section></main>;
}
