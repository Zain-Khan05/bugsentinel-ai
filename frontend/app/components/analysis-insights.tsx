type Finding = { severity: string; category: string; line: number; message: string };
type FileReport = { filename: string; language: string; metrics: { lines_of_code: number; function_count: number; cyclomatic_complexity: number; duplicate_lines: number; todo_count: number }; prediction: { model: string; contributing_factors: string[] }; findings: Finding[] };
type Report = { summary: { files_analyzed: number; total_lines_of_code: number; average_complexity: number; quality_findings: number }; files: FileReport[] };

export function AnalysisInsights({ report }: { report: Report }) {
  const primaryFile = report.files[0];
  if (!primaryFile) return null;
  const { metrics, prediction } = primaryFile;
  return <section className="analysis-insights"><div className="insight-summary"><span>{report.summary.total_lines_of_code} LOC</span><span>{metrics.function_count} functions</span><span>Complexity {metrics.cyclomatic_complexity}</span><span>{report.summary.quality_findings} quality signals</span></div><div className="prediction-card"><p>MODEL: {prediction.model}</p><strong>Why this score</strong><ul>{prediction.contributing_factors.map((factor) => <li key={factor}>{factor}</li>)}</ul></div><details className="metrics-details"><summary>View file metrics</summary><div><span>Language <b>{primaryFile.language}</b></span><span>Duplicate lines <b>{metrics.duplicate_lines}</b></span><span>TODO markers <b>{metrics.todo_count}</b></span></div></details></section>;
}
