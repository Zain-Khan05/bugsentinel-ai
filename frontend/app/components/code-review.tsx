'use client';

import { useEffect, useMemo, useState } from 'react';

type Finding = { severity: string; category: string; line: number; message: string };
type SourceFile = { filename: string; content: string };
type FileReport = { filename: string; findings: Finding[] };

const severityRank: Record<string, number> = { high: 3, medium: 2, low: 1 };

export function CodeReview({ sources, reports }: { sources: SourceFile[]; reports: FileReport[] }) {
  const visibleSources = sources.filter((source) => reports.some((report) => report.filename === source.filename));
  const [activeFilename, setActiveFilename] = useState(visibleSources[0]?.filename || '');

  useEffect(() => {
    if (!visibleSources.some((source) => source.filename === activeFilename)) setActiveFilename(visibleSources[0]?.filename || '');
  }, [activeFilename, visibleSources]);

  const activeSource = visibleSources.find((source) => source.filename === activeFilename);
  const activeReport = reports.find((report) => report.filename === activeFilename);
  const findingsByLine = useMemo(() => {
    const result = new Map<number, Finding[]>();
    activeReport?.findings.filter((finding) => finding.line > 0).forEach((finding) => {
      result.set(finding.line, [...(result.get(finding.line) || []), finding]);
    });
    return result;
  }, [activeReport]);

  if (!visibleSources.length || !activeSource || !activeReport) {
    return <section className="code-review empty-review"><strong>Source preview unavailable</strong><p>This older report has findings, but its original source code was not stored.</p></section>;
  }

  return <section className="code-review">
    <div className="code-review-heading"><div><p className="eyebrow">LINE-BY-LINE REVIEW</p><h3>Findings in source</h3></div><span>{activeReport.findings.filter((finding) => finding.line > 0).length} LOCATIONS</span></div>
    {visibleSources.length > 1 && <div className="file-tabs" role="tablist" aria-label="Analyzed source files">{visibleSources.map((source) => <button key={source.filename} type="button" role="tab" aria-selected={source.filename === activeFilename} className={source.filename === activeFilename ? 'active' : ''} onClick={() => setActiveFilename(source.filename)}>{source.filename}</button>)}</div>}
    <div className="code-legend"><span className="legend-high">High</span><span className="legend-medium">Medium</span><span className="legend-low">Low</span><small>Highlighted lines contain detected findings.</small></div>
    <div className="code-frame" data-testid="code-review">{activeSource.content.split('\n').map((line, index) => {
      const lineNumber = index + 1;
      const lineFindings = findingsByLine.get(lineNumber) || [];
      const strongest = lineFindings.reduce((current, finding) => severityRank[finding.severity] > severityRank[current] ? finding.severity : current, 'low');
      return <div className={`code-line ${lineFindings.length ? `flagged flagged-${strongest}` : ''}`} key={`${lineNumber}-${line}`}><span className="line-number">{lineNumber}</span><code>{line || ' '}</code>{lineFindings.length > 0 && <span className="line-flags">{lineFindings.map((finding) => <span key={`${finding.category}-${finding.message}`} title={`${finding.category}: ${finding.message}`}>{finding.severity}: {finding.message}</span>)}</span>}</div>;
    })}</div>
    {activeReport.findings.some((finding) => finding.line === 0) && <p className="code-note">Some project-level findings, such as repeated-code detection, do not map to one exact line.</p>}
  </section>;
}
