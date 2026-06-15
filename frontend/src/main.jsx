import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Download, FileSpreadsheet, Play, RefreshCw } from 'lucide-react';
import { fetchDatabases, fetchReports, fileDownloadUrl, generateReport } from './api';
import './styles.css';

const DEFAULT_FILTERS = '{\n  "has_activity": "true"\n}';

function parseFilters(value) {
  const trimmed = value.trim();
  if (!trimmed) return {};
  return JSON.parse(trimmed);
}

function App() {
  const [reports, setReports] = useState([]);
  const [databases, setDatabases] = useState([]);
  const [reportId, setReportId] = useState('');
  const [database, setDatabase] = useState('');
  const [outputFormat, setOutputFormat] = useState('excel');
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  async function loadData() {
    setLoading(true);
    setError('');
    try {
      const [reportsPayload, databasesPayload] = await Promise.all([
        fetchReports(),
        fetchDatabases(),
      ]);
      const nextReports = reportsPayload.reports || [];
      const nextDatabases = databasesPayload.databases || [];
      setReports(nextReports);
      setDatabases(nextDatabases);
      setReportId((current) => current || nextReports[0]?.id || '');
      setDatabase((current) => current || nextDatabases[0]?.name || '');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const selectedReport = useMemo(
    () => reports.find((report) => report.id === reportId),
    [reports, reportId],
  );

  const selectedDatabase = useMemo(
    () => databases.find((item) => item.name === database),
    [databases, database],
  );

  async function onGenerate(event) {
    event.preventDefault();
    setGenerating(true);
    setError('');
    setResult(null);

    try {
      const payload = await generateReport({
        report_id: reportId,
        database,
        output_format: outputFormat,
        filters: parseFilters(filters),
      });
      setResult(payload);
    } catch (err) {
      setError(err.message);
    } finally {
      setGenerating(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">RX_PM</p>
          <h1>Report Console</h1>
        </div>
        <button className="icon-button" type="button" onClick={loadData} disabled={loading} title="Refresh">
          <RefreshCw size={18} />
        </button>
      </header>

      {error ? <div className="alert">{error}</div> : null}

      <section className="workspace">
        <form className="panel" onSubmit={onGenerate}>
          <div className="field">
            <label htmlFor="report">Report</label>
            <select id="report" value={reportId} onChange={(event) => setReportId(event.target.value)}>
              {reports.map((report) => (
                <option key={report.id} value={report.id}>
                  {report.name}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label htmlFor="database">Database</label>
            <select id="database" value={database} onChange={(event) => setDatabase(event.target.value)}>
              {databases.map((item) => (
                <option key={item.name} value={item.name}>
                  {item.name}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label htmlFor="format">Format</label>
            <select id="format" value={outputFormat} onChange={(event) => setOutputFormat(event.target.value)}>
              <option value="excel">Excel</option>
              <option value="csv">CSV</option>
              <option value="json">JSON</option>
            </select>
          </div>

          <div className="field">
            <label htmlFor="filters">Filters JSON</label>
            <textarea
              id="filters"
              value={filters}
              onChange={(event) => setFilters(event.target.value)}
              spellCheck="false"
            />
          </div>

          <button className="primary-button" type="submit" disabled={!reportId || !database || generating}>
            <Play size={18} />
            {generating ? 'Generating' : 'Generate'}
          </button>
        </form>

        <aside className="details">
          <div className="details-header">
            <FileSpreadsheet size={20} />
            <h2>{selectedReport?.name || 'Report'}</h2>
          </div>
          <p>{selectedReport?.description || 'Choose a report to view its details.'}</p>

          <dl>
            <dt>Category</dt>
            <dd>{selectedReport?.category || '-'}</dd>
            <dt>Filters</dt>
            <dd>{selectedReport?.available_filters?.join(', ') || 'None'}</dd>
            <dt>Output</dt>
            <dd>{selectedDatabase?.output_path || '-'}</dd>
          </dl>

          {result ? (
            <a className="download-link" href={fileDownloadUrl(result.output_file)}>
              <Download size={18} />
              Download {result.output_format.toUpperCase()}
            </a>
          ) : null}
        </aside>
      </section>
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);
