import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Activity,
  Database,
  Download,
  Play,
  RefreshCw,
  Sparkles,
  Table2,
} from 'lucide-react';
import {
  downloadReportFile,
  fetchDashboardInsights,
  fetchDatabases,
  fetchReportPreview,
  fetchReports,
  generateReport,
  updateDatabaseSelection,
} from './api';
import ConnectionsPanel from './ConnectionsPanel';
import { loadDashboardPrefs, rememberProjectSelection, rememberReportSelection } from './sessionPrefs';
import './styles.css';

const PROJECT_ORDER = ['AG', 'LMS', 'Telios', 'Language', 'Utility'];
const PROJECT_LABELS = {
  AG: 'AG',
  LMS: 'LMS',
  Telios: 'Telios',
  Language: 'Language',
  Utility: 'Utility',
};
const SUB_TABS = [
  { id: 'data', label: 'Data', icon: Table2 },
  { id: 'generate', label: 'Generate', icon: Play },
  { id: 'history', label: 'History', icon: Activity },
];

const FORMAT_LABELS = {
  excel: 'Excel',
  csv: 'CSV',
  json: 'JSON',
};

function formatLabel(format) {
  return FORMAT_LABELS[format] || format;
}

function displayOutputPath(fullPath) {
  if (!fullPath) return '';
  const normalized = fullPath.replace(/\\/g, '/');
  const backendOutput = normalized.indexOf('/backend/output/');
  if (backendOutput >= 0) {
    return normalized.slice(backendOutput + 1);
  }
  const outputOnly = normalized.indexOf('/output/');
  if (outputOnly >= 0) {
    return `backend${normalized.slice(outputOnly)}`;
  }
  return normalized;
}

function outputFileName(fullPath) {
  if (!fullPath) return 'report';
  return fullPath.split(/[/\\]/).pop() || fullPath;
}

function groupByProject(reports) {
  return reports.reduce((groups, report) => {
    const key = report.category || 'Utility';
    groups[key] = groups[key] || [];
    groups[key].push(report);
    return groups;
  }, {});
}

function pickDatabaseForProject(databases, activeNames, project, preferredName = '') {
  const scoped = activeProjectDatabases(databases, activeNames, project);
  if (!scoped.length) return '';
  if (preferredName && scoped.some((item) => item.name === preferredName)) {
    return preferredName;
  }
  return scoped[0].name;
}

function resolveProjectDatabase(databases, activeNames, project, primaryName, selectedByProject = {}) {
  const preferred = selectedByProject[project] || '';
  return pickDatabaseForProject(databases, activeNames, project, preferred || primaryName);
}

function activeProjectDatabases(databases, activeNames, project) {
  const activeSet = new Set(activeNames);
  return databases.filter((item) => activeSet.has(item.name) && item.category === project);
}

function filtersFromRows(rows) {
  return rows.reduce((filters, row) => {
    if (row.enabled && row.key.trim()) {
      filters[row.key.trim()] = row.value;
    }
    return filters;
  }, {});
}

function rowsFromReport(report) {
  const filters = report?.available_filters || [];
  if (!filters.length) return [];
  return filters.map((key) => ({
    key,
    value: key === 'has_activity' ? 'true' : '',
    enabled: key === 'has_activity',
  }));
}

function parseJsonFilters(value) {
  const trimmed = value.trim();
  if (!trimmed) return {};
  return JSON.parse(trimmed);
}

function formatCell(value) {
  if (value === null || value === undefined || value === '') return '—';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

function InsightMetric({ metric, onOpen }) {
  return (
    <button
      className="insight-metric"
      type="button"
      onClick={() => onOpen(metric)}
      title={metric.description || metric.label}
    >
      <span>{metric.label}</span>
      <strong>{metric.status === 'error' ? '—' : metric.display_value}</strong>
    </button>
  );
}

function DbSummaryPanel({
  previewSourceName,
  dbStats,
  currentInsights,
  reportInsights,
  isLoading,
  onRefresh,
  onOpenInsight,
}) {
  return (
    <div className="db-summary">
      <div className="section-heading">
        <div className="data-meta">
          <Sparkles size={16} />
          <span>{previewSourceName}</span>
          {isLoading ? <span>Loading…</span> : null}
        </div>
        <button
          className="secondary-button"
          type="button"
          onClick={onRefresh}
          disabled={isLoading}
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      <div className="stats-grid compact">
        {dbStats.map((stat) => (
          <div className="metric" key={stat.label}>
            <span>{stat.label}</span>
            <strong>{stat.value}</strong>
          </div>
        ))}
      </div>

      {isLoading && !currentInsights?.metrics?.length ? (
        <div className="insights-row loading">Loading insights…</div>
      ) : currentInsights?.metrics?.length ? (
        <div className="insights-row">
          {currentInsights.metrics.map((metric) => (
            <InsightMetric key={metric.id} metric={metric} onOpen={onOpenInsight} />
          ))}
        </div>
      ) : null}

      {reportInsights.length ? (
        <div className="report-insights">
          <span>Related to this report:</span>
          <div className="insights-row inline">
            {reportInsights.map((metric) => (
              <InsightMetric key={metric.id} metric={metric} onOpen={onOpenInsight} />
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function DataTable({ sheet }) {
  if (!sheet?.columns?.length) {
    return <div className="empty-state">No columns available</div>;
  }

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {sheet.columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sheet.rows.length ? (
            sheet.rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {sheet.columns.map((column) => (
                  <td key={`${rowIndex}-${column}`}>{formatCell(row[column])}</td>
                ))}
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={sheet.columns.length}>No rows returned</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function App() {
  const [reports, setReports] = useState([]);
  const [databases, setDatabases] = useState([]);
  const [project, setProject] = useState('AG');
  const [reportId, setReportId] = useState('');
  const [subTab, setSubTab] = useState('data');
  const [database, setDatabase] = useState('');
  const [activeDatabases, setActiveDatabases] = useState([]);
  const [primaryDatabase, setPrimaryDatabase] = useState('');
  const [selectedByProject, setSelectedByProject] = useState({});
  const [previewDatabase, setPreviewDatabase] = useState('');
  const [prefsReady, setPrefsReady] = useState(false);
  const [connectionsOpen, setConnectionsOpen] = useState(false);
  const [outputFormat, setOutputFormat] = useState('excel');
  const [filterRows, setFilterRows] = useState([]);
  const [jsonMode, setJsonMode] = useState(false);
  const [jsonFilters, setJsonFilters] = useState('{}');
  const [sheetTab, setSheetTab] = useState('');
  const [history, setHistory] = useState([]);
  const [reportCache, setReportCache] = useState({});
  const [insightsCache, setInsightsCache] = useState({});
  const [loadingDbs, setLoadingDbs] = useState({});
  const [loadingInsightDbs, setLoadingInsightDbs] = useState({});
  const pendingInsightRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [downloadStatus, setDownloadStatus] = useState(null);
  const [error, setError] = useState('');

  async function applyDatabasePayload(databasesPayload, { invalidateCaches = true } = {}) {
    const nextDatabases = databasesPayload.databases || [];
    const nextActive = databasesPayload.active || nextDatabases.map((item) => item.name);
    const nextPrimary = databasesPayload.primary || nextActive[0] || '';
    const nextSelected = databasesPayload.selected_by_project || {};

    setDatabases(nextDatabases);
    setActiveDatabases(nextActive);
    setPrimaryDatabase(nextPrimary);
    setSelectedByProject(nextSelected);

    if (invalidateCaches) {
      const activeSet = new Set(nextActive);
      setReportCache((prev) => Object.fromEntries(
        Object.entries(prev).filter(([key]) => {
          const parts = key.split('|');
          return parts.length >= 2 && activeSet.has(parts[1]);
        }),
      ));
      setInsightsCache((prev) => Object.fromEntries(
        Object.entries(prev).filter(([key]) => {
          const dbName = key.split('|')[1];
          return dbName && activeSet.has(dbName);
        }),
      ));
    }

    setPreviewDatabase((current) => {
      const projectDbs = activeProjectDatabases(nextDatabases, nextActive, project);
      if (current && projectDbs.some((item) => item.name === current)) return current;
      return resolveProjectDatabase(nextDatabases, nextActive, project, nextPrimary, nextSelected)
        || pickDatabaseForProject(nextDatabases, nextActive, project, nextPrimary);
    });
    setDatabase((current) => {
      const projectDbs = activeProjectDatabases(nextDatabases, nextActive, project);
      if (current && projectDbs.some((item) => item.name === current)) return current;
      return resolveProjectDatabase(nextDatabases, nextActive, project, nextPrimary, nextSelected)
        || pickDatabaseForProject(nextDatabases, nextActive, project, nextPrimary);
    });
    return nextDatabases;
  }

  async function loadReportsCatalog(projectHint = '') {
    const reportsPayload = await fetchReports();
    const nextReports = reportsPayload.reports || [];
    const grouped = groupByProject(nextReports);
    const prefs = loadDashboardPrefs();
    const firstProject = PROJECT_ORDER.find((item) => grouped[item]?.length) || Object.keys(grouped)[0] || 'AG';
    const preferredProject = projectHint || prefs.project;
    const nextProject = preferredProject && grouped[preferredProject]?.length
      ? preferredProject
      : firstProject;
    const savedReportId = prefs.reportByProject?.[nextProject];
    const projectReportsForHint = grouped[nextProject] || [];
    const nextReportId = savedReportId && nextReports.some((report) => report.id === savedReportId)
      ? savedReportId
      : projectReportsForHint[0]?.id || '';

    setReports(nextReports);
    setProject(nextProject);
    setReportId(nextReportId);
    return nextReports;
  }

  async function bootstrap() {
    setLoading(true);
    setError('');
    try {
      const prefs = loadDashboardPrefs();
      const databasesPayload = await fetchDatabases();
      const nextDatabases = databasesPayload.databases || [];
      const nextActive = databasesPayload.active || nextDatabases.map((item) => item.name);
      const nextPrimary = databasesPayload.primary || nextActive[0] || '';
      const nextSelected = databasesPayload.selected_by_project || {};

      setDatabases(nextDatabases);
      setActiveDatabases(nextActive);
      setPrimaryDatabase(nextPrimary);
      setSelectedByProject(nextSelected);

      const nextReports = await loadReportsCatalog(prefs.project);
      const grouped = groupByProject(nextReports);
      const firstProject = PROJECT_ORDER.find((item) => grouped[item]?.length) || Object.keys(grouped)[0] || 'AG';
      const initialProject = prefs.project && grouped[prefs.project]?.length ? prefs.project : firstProject;
      const initialDatabase = resolveProjectDatabase(
        nextDatabases,
        nextActive,
        initialProject,
        nextPrimary,
        nextSelected,
      );
      setPreviewDatabase(initialDatabase);
      setDatabase(initialDatabase);
      setPrefsReady(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function reloadDashboard() {
    setLoading(true);
    setError('');
    try {
      await applyDatabasePayload(await fetchDatabases());
      await loadReportsCatalog();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    bootstrap();
  }, []);

  const groupedReports = useMemo(() => groupByProject(reports), [reports]);
  const projects = useMemo(() => {
    const ordered = PROJECT_ORDER.filter((item) => groupedReports[item]?.length);
    const extra = Object.keys(groupedReports).filter((item) => !PROJECT_ORDER.includes(item));
    return [...ordered, ...extra];
  }, [groupedReports]);

  const projectReports = groupedReports[project] || [];
  const selectedReport = reports.find((report) => report.id === reportId) || projectReports[0];
  const activeProjectDbList = useMemo(
    () => activeProjectDatabases(databases, activeDatabases, project),
    [databases, activeDatabases, project],
  );

  const defaultProjectDatabase = useMemo(
    () => resolveProjectDatabase(databases, activeDatabases, project, primaryDatabase, selectedByProject),
    [databases, activeDatabases, project, primaryDatabase, selectedByProject],
  );

  const previewSourceName = activeProjectDbList.some((item) => item.name === previewDatabase)
    ? previewDatabase
    : defaultProjectDatabase;

  useEffect(() => {
    if (!activeProjectDbList.length) {
      setPreviewDatabase((current) => (current ? '' : current));
      setDatabase((current) => (current ? '' : current));
      return;
    }

    setPreviewDatabase((current) => {
      if (current && activeProjectDbList.some((item) => item.name === current)) {
        return current;
      }
      return defaultProjectDatabase || activeProjectDbList[0].name;
    });
    setDatabase((current) => {
      if (current && activeProjectDbList.some((item) => item.name === current)) {
        return current;
      }
      return defaultProjectDatabase || activeProjectDbList[0].name;
    });
  }, [activeProjectDbList, defaultProjectDatabase]);

  useEffect(() => {
    if (projectReports.length && !projectReports.some((report) => report.id === reportId)) {
      setReportId(projectReports[0].id);
    }
  }, [project, reports, projectReports, reportId]);

  useEffect(() => {
    if (!selectedReport) return;

    if (pendingInsightRef.current) {
      const pending = pendingInsightRef.current;
      pendingInsightRef.current = null;
      const available = selectedReport.available_filters || [];
      if (Object.keys(pending.filters || {}).length && available.length) {
        const presetKeys = new Set(Object.keys(pending.filters));
        setFilterRows(available.map((key) => ({
          key,
          value: pending.filters[key] ?? (key === 'has_activity' ? 'true' : ''),
          enabled: presetKeys.has(key) ? Boolean(pending.filters[key]) : key === 'has_activity',
        })));
        setJsonFilters(JSON.stringify(pending.filters));
      } else {
        setFilterRows(rowsFromReport(selectedReport));
        setJsonFilters('{}');
      }
      if (pending.sheet) setSheetTab(pending.sheet);
      setSubTab('data');
      if (pending.loadDb) {
        loadReportDataForDatabase(pending.loadDb);
        loadInsightsForDatabase(pending.loadDb);
      }
      return;
    }

    setFilterRows(rowsFromReport(selectedReport));
    setJsonFilters('{}');
    setSheetTab(selectedReport.sheets?.[0] || 'Data');
  }, [selectedReport?.id]);

  const activeFilters = useMemo(() => {
    try {
      return jsonMode ? parseJsonFilters(jsonFilters) : filtersFromRows(filterRows);
    } catch {
      return {};
    }
  }, [filterRows, jsonFilters, jsonMode]);

  const filtersKey = useMemo(() => JSON.stringify(activeFilters), [activeFilters]);

  function buildCacheKey(dbName) {
    return `${selectedReport?.id || ''}|${dbName}|${filtersKey}`;
  }

  function getCachedSheets(dbName) {
    return reportCache[buildCacheKey(dbName)] || null;
  }

  function isDbLoaded(dbName) {
    return Boolean(getCachedSheets(dbName));
  }

  const currentDbSheets = useMemo(
    () => getCachedSheets(previewSourceName),
    [reportCache, previewSourceName, filtersKey, selectedReport?.id],
  );

  const sheetNames = useMemo(() => {
    if (currentDbSheets) return Object.keys(currentDbSheets);
    if (selectedReport?.sheets?.length) return selectedReport.sheets;
    return ['Data'];
  }, [currentDbSheets, selectedReport]);

  const activeSheet = currentDbSheets?.[sheetTab] || null;
  const isCurrentDbLoading = Boolean(loadingDbs[previewSourceName]);
  const isCurrentInsightsLoading = Boolean(loadingInsightDbs[previewSourceName]);

  const insightsKey = previewSourceName ? `${project}|${previewSourceName}` : '';
  const currentInsights = insightsKey ? insightsCache[insightsKey] : null;

  const dbSummaryVisible = Boolean(
    isDbLoaded(previewSourceName)
    || currentInsights
    || isCurrentDbLoading
    || isCurrentInsightsLoading,
  );

  const dbStats = useMemo(() => {
    const loadedRows = currentDbSheets
      ? Object.values(currentDbSheets).reduce((sum, sheet) => sum + (sheet.total_rows || 0), 0)
      : null;
    return [
      { label: 'Database', value: previewSourceName || '—' },
      { label: 'Sheets', value: currentDbSheets ? Object.keys(currentDbSheets).length : '—' },
      { label: 'Rows', value: loadedRows ?? '—' },
      { label: 'Insights', value: currentInsights?.metrics?.length ?? '—' },
    ];
  }, [currentDbSheets, currentInsights, previewSourceName]);

  const reportInsights = useMemo(() => {
    if (!currentInsights?.metrics?.length || !selectedReport) return [];
    return currentInsights.metrics.filter(
      (metric) =>
        metric.navigate?.report_id === selectedReport.id
        || metric.source_report_id === selectedReport.id,
    );
  }, [currentInsights, selectedReport]);

  async function loadInsightsForDatabase(dbName, { force = false } = {}) {
    if (!dbName || !activeDatabases.includes(dbName)) return null;

    const key = `${project}|${dbName}`;
    if (!force && insightsCache[key]) return insightsCache[key];

    setLoadingInsightDbs((prev) => ({ ...prev, [dbName]: true }));
    try {
      const payload = await fetchDashboardInsights(project, dbName, force);
      setInsightsCache((prev) => ({ ...prev, [key]: payload }));
      return payload;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setLoadingInsightDbs((prev) => ({ ...prev, [dbName]: false }));
    }
  }

  async function refreshActiveDatabase() {
    await Promise.all([
      loadInsightsForDatabase(previewSourceName, { force: true }),
      isDbLoaded(previewSourceName)
        ? loadReportDataForDatabase(previewSourceName, { force: true })
        : loadReportDataForDatabase(previewSourceName),
    ]);
  }

  async function loadReportDataForDatabase(dbName, { force = false } = {}) {
    if (!selectedReport || !dbName || !activeDatabases.includes(dbName)) return null;

    const key = buildCacheKey(dbName);
    if (!force && reportCache[key]) {
      return reportCache[key];
    }

    setLoadingDbs((prev) => ({ ...prev, [dbName]: true }));
    setError('');
    try {
      const payload = await fetchReportPreview({
        report_id: selectedReport.id,
        database: dbName,
        filters: activeFilters,
      });
      const sheets = payload.results?.[dbName] || payload.sheets || {};
      setReportCache((prev) => ({ ...prev, [key]: sheets }));
      if (dbName === previewSourceName) {
        const nextSheets = Object.keys(sheets);
        if (nextSheets.length && !nextSheets.includes(sheetTab)) {
          setSheetTab(nextSheets[0]);
        }
      }
      return sheets;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setLoadingDbs((prev) => ({ ...prev, [dbName]: false }));
    }
  }

  useEffect(() => {
    if (!prefsReady || !selectedReport || !previewSourceName || subTab !== 'data') return;
    if (!activeDatabases.includes(previewSourceName)) return;
    loadInsightsForDatabase(previewSourceName);
    loadReportDataForDatabase(previewSourceName);
  }, [prefsReady, selectedReport?.id, previewSourceName, filtersKey, subTab, activeDatabases]);

  async function selectPreviewDatabase(dbName) {
    if (!activeDatabases.includes(dbName)) return;
    setPreviewDatabase(dbName);
    setDatabase(dbName);
    setSubTab('data');
    setSelectedByProject((prev) => ({ ...prev, [project]: dbName }));
    try {
      const payload = await updateDatabaseSelection(project, dbName);
      setSelectedByProject(payload.selected_by_project || { ...selectedByProject, [project]: dbName });
    } catch (err) {
      setError(err.message);
    }
  }

  function openInsightReport(metric) {
    const navigate = metric.navigate || {};
    if (!navigate.report_id) return;

    pendingInsightRef.current = {
      filters: navigate.filters || {},
      sheet: navigate.sheet,
      loadDb: previewSourceName || undefined,
    };
    setReportId(navigate.report_id);
  }

  function updateFilterRow(index, patch) {
    setFilterRows((rows) => rows.map((row, rowIndex) => (rowIndex === index ? { ...row, ...patch } : row)));
  }

  function addCustomFilter() {
    setFilterRows((rows) => [...rows, { key: '', value: '', enabled: true }]);
  }

  async function onGenerate(event) {
    event.preventDefault();
    setGenerating(true);
    setError('');
    const label = formatLabel(outputFormat);

    setDownloadStatus({
      phase: 'generating',
      format: outputFormat,
      message: `Generating ${label} report…`,
      serverPath: '',
      fileName: '',
      browserHint: '',
    });

    try {
      const filters = jsonMode ? parseJsonFilters(jsonFilters) : filtersFromRows(filterRows);
      const payload = await generateReport({
        report_id: selectedReport.id,
        databases: activeProjectDbList.map((item) => item.name),
        output_format: outputFormat,
        filters,
      });
      const outputs = payload.outputs || [];
      setHistory((items) => [
        ...outputs.map((output) => ({
          ...output,
          project,
          reportName: selectedReport.name,
          databaseName: output.database,
          filters,
          createdAt: new Date().toLocaleString(),
        })),
        ...items,
      ]);
      setSubTab('history');

      for (const output of outputs) {
        const serverPath = displayOutputPath(output.output_file);
        const fileName = outputFileName(output.output_file);
        const outputLabel = formatLabel(output.output_format || outputFormat);

        setDownloading(true);
        setDownloadStatus({
          phase: 'downloading',
          format: output.output_format || outputFormat,
          message: `Downloading ${outputLabel} report…`,
          serverPath,
          fileName,
          browserHint: `Saving to your browser Downloads folder as "${fileName}"`,
        });

        await downloadReportFile(output.output_file);
      }

      if (outputs.length) {
        const last = outputs[outputs.length - 1];
        const outputLabel = formatLabel(last.output_format || outputFormat);
        setDownloadStatus({
          phase: 'complete',
          format: last.output_format || outputFormat,
          message: outputs.length === 1
            ? `${outputLabel} report downloaded`
            : `${outputs.length} ${outputLabel} reports downloaded`,
          serverPath: displayOutputPath(last.output_file),
          fileName: outputFileName(last.output_file),
          browserHint: outputs.length === 1
            ? `Saved to your browser Downloads folder as "${outputFileName(last.output_file)}"`
            : `Saved ${outputs.length} files to your browser Downloads folder`,
        });
        window.setTimeout(() => setDownloadStatus(null), 10000);
      } else {
        setDownloadStatus(null);
      }
    } catch (err) {
      setError(err.message);
      setDownloadStatus(null);
    } finally {
      setGenerating(false);
      setDownloading(false);
    }
  }

  async function onDownloadHistoryItem(item) {
    setError('');
    const label = formatLabel(item.output_format || 'excel');
    const serverPath = displayOutputPath(item.output_file);
    const fileName = outputFileName(item.output_file);

    setDownloading(true);
    setDownloadStatus({
      phase: 'downloading',
      format: item.output_format || 'excel',
      message: `Downloading ${label} report…`,
      serverPath,
      fileName,
      browserHint: `Saving to your browser Downloads folder as "${fileName}"`,
    });

    try {
      await downloadReportFile(item.output_file);
      setDownloadStatus({
        phase: 'complete',
        format: item.output_format || 'excel',
        message: `${label} report downloaded`,
        serverPath,
        fileName,
        browserHint: `Saved to your browser Downloads folder as "${fileName}"`,
      });
      window.setTimeout(() => setDownloadStatus(null), 10000);
    } catch (err) {
      setError(err.message);
      setDownloadStatus(null);
    } finally {
      setDownloading(false);
    }
  }

  return (
    <main className="dashboard-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">RX_PM</p>
          <h1>Reporting Dashboard</h1>
        </div>
        <div className="topbar-actions">
          <button className="secondary-button" type="button" onClick={() => setConnectionsOpen(true)}>
            <Database size={16} />
            Connections ({activeDatabases.length})
          </button>
          <button className="icon-button" type="button" onClick={reloadDashboard} disabled={loading} title="Refresh">
            <RefreshCw size={18} />
          </button>
        </div>
      </header>

      {error ? <div className="alert">{error}</div> : null}

      {downloadStatus ? (
        <div className={`download-status download-status--${downloadStatus.phase}`}>
          <div className="download-status__header">
            <Download size={18} />
            <strong>{downloadStatus.message}</strong>
          </div>
          {downloadStatus.serverPath ? (
            <p className="download-status__path">
              <span>Generated file:</span>
              <code>{downloadStatus.serverPath}</code>
            </p>
          ) : null}
          {downloadStatus.browserHint ? (
            <p className="download-status__hint">{downloadStatus.browserHint}</p>
          ) : null}
        </div>
      ) : null}

      <section className="flow-strip">
        <span>1. Configure connections</span>
        <span>2. Select a report</span>
        <span>3. Data loads automatically for your selected database</span>
      </section>

      <nav className="project-tabs" aria-label="Projects">
        {projects.map((item) => (
          <button
            className={item === project ? 'tab active' : 'tab'}
            key={item}
            type="button"
            onClick={() => {
              rememberProjectSelection(item);
              const nextDb = resolveProjectDatabase(
                databases,
                activeDatabases,
                item,
                primaryDatabase,
                selectedByProject,
              );
              setProject(item);
              setPreviewDatabase(nextDb);
              setDatabase(nextDb);
              setSubTab('data');
              const grouped = groupByProject(reports);
              const savedReportId = loadDashboardPrefs().reportByProject?.[item];
              const reportsForProject = grouped[item] || [];
              if (savedReportId && reportsForProject.some((report) => report.id === savedReportId)) {
                setReportId(savedReportId);
              } else if (reportsForProject.length) {
                setReportId(reportsForProject[0].id);
              }
              if (nextDb) {
                setSelectedByProject((prev) => ({ ...prev, [item]: nextDb }));
                updateDatabaseSelection(item, nextDb).then((payload) => {
                  setSelectedByProject(payload.selected_by_project || {});
                }).catch((err) => setError(err.message));
              }
            }}
          >
            {PROJECT_LABELS[item] || item}
          </button>
        ))}
      </nav>

      {activeProjectDbList.length ? (
        <section className="project-db-bar">
          <div className="database-tabs">
            {activeProjectDbList.map((item) => (
              <button
                className={[
                  'sheet-tab',
                  item.name === previewDatabase ? 'active' : '',
                  isDbLoaded(item.name) || insightsCache[`${project}|${item.name}`] ? 'loaded' : '',
                ].filter(Boolean).join(' ')}
                disabled={loadingDbs[item.name] || loadingInsightDbs[item.name]}
                key={item.name}
                type="button"
                onClick={() => selectPreviewDatabase(item.name)}
              >
                {item.name}
                {loadingDbs[item.name] || loadingInsightDbs[item.name] ? <small>loading</small> : null}
              </button>
            ))}
          </div>

          {dbSummaryVisible ? (
            <DbSummaryPanel
              previewSourceName={previewSourceName}
              dbStats={dbStats}
              currentInsights={currentInsights}
              reportInsights={reportInsights}
              isLoading={isCurrentDbLoading || isCurrentInsightsLoading}
              onRefresh={refreshActiveDatabase}
              onOpenInsight={openInsightReport}
            />
          ) : (
            <div className="db-summary-hint">
              Loading data for {previewSourceName || defaultProjectDatabase || 'selected database'}…
            </div>
          )}
        </section>
      ) : null}

      <section className="dashboard-grid">
        <aside className="report-nav">
          <div className="section-title">Reports</div>
          {projectReports.map((report) => (
            <button
              className={report.id === selectedReport?.id ? 'report-tab active' : 'report-tab'}
              key={report.id}
              type="button"
              onClick={() => {
                setReportId(report.id);
                rememberReportSelection(project, report.id);
                setSubTab('data');
              }}
            >
              <span>{report.name}</span>
            </button>
          ))}
        </aside>

        <section className="workbench">
          <header className="report-header">
            <div>
              <h2>{selectedReport?.name || 'Report'}</h2>
              {selectedReport?.description ? <p>{selectedReport.description}</p> : null}
            </div>
          </header>

          <nav className="sub-tabs" aria-label="Report sections">
            {SUB_TABS.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  className={item.id === subTab ? 'sub-tab active' : 'sub-tab'}
                  key={item.id}
                  type="button"
                  onClick={() => setSubTab(item.id)}
                >
                  <Icon size={16} />
                  {item.label}
                </button>
              );
            })}
          </nav>

          {subTab === 'data' ? (
            <div className="surface">
              {!activeProjectDbList.length ? (
                <div className="empty-state">
                  No active databases for {PROJECT_LABELS[project] || project}. Open Connections to enable one.
                </div>
              ) : (
                <>
                  <div className="sheet-tabs">
                    {sheetNames.map((sheet) => (
                      <button
                        className={sheet === sheetTab ? 'sheet-tab active' : 'sheet-tab'}
                        key={sheet}
                        type="button"
                        onClick={() => setSheetTab(sheet)}
                        disabled={!currentDbSheets}
                      >
                        {sheet}
                      </button>
                    ))}
                  </div>

                  {isCurrentDbLoading ? (
                    <div className="empty-state">Loading {previewSourceName}…</div>
                  ) : activeSheet ? (
                    <>
                      <div className="section-heading">
                        <div className="data-meta">
                          <span>{activeSheet.total_rows} rows</span>
                          {activeSheet.truncated ? (
                            <span>Showing first {activeSheet.rows.length}</span>
                          ) : null}
                        </div>
                      </div>
                      <DataTable sheet={activeSheet} />
                    </>
                  ) : (
                    <div className="data-preview">
                      <Table2 size={22} />
                      <strong>Loading report data</strong>
                      <span>Preview loads automatically for {previewSourceName || 'the selected database'}</span>
                    </div>
                  )}
                </>
              )}
            </div>
          ) : null}

          {subTab === 'generate' ? (
            <form className="surface generator" onSubmit={onGenerate}>
              <p className="generate-note">
                Export runs against active databases:{' '}
                {activeProjectDbList.length
                  ? activeProjectDbList.map((item) => item.name).join(', ')
                  : 'none selected'}
              </p>
              <div className="form-row">
                <div className="field">
                  <label htmlFor="format">Format</label>
                  <select id="format" value={outputFormat} onChange={(event) => setOutputFormat(event.target.value)}>
                    <option value="excel">Excel</option>
                    <option value="csv">CSV</option>
                    <option value="json">JSON</option>
                  </select>
                </div>
                <label className="toggle">
                  <input type="checkbox" checked={jsonMode} onChange={(event) => setJsonMode(event.target.checked)} />
                  JSON filters
                </label>
              </div>

              {jsonMode ? (
                <textarea
                  className="json-editor"
                  value={jsonFilters}
                  onChange={(event) => setJsonFilters(event.target.value)}
                  spellCheck="false"
                />
              ) : (
                <div className="filter-table">
                  {filterRows.length ? filterRows.map((row, index) => (
                    <div className="filter-row" key={`${row.key}-${index}`}>
                      <input
                        aria-label="Enable filter"
                        checked={row.enabled}
                        type="checkbox"
                        onChange={(event) => updateFilterRow(index, { enabled: event.target.checked })}
                      />
                      <input
                        aria-label="Filter name"
                        value={row.key}
                        onChange={(event) => updateFilterRow(index, { key: event.target.value })}
                        placeholder="filter"
                      />
                      <input
                        aria-label="Filter value"
                        value={row.value}
                        onChange={(event) => updateFilterRow(index, { value: event.target.value })}
                        placeholder="value"
                      />
                    </div>
                  )) : (
                    <div className="empty-state compact">This report has no filters</div>
                  )}
                  <button className="secondary-button" type="button" onClick={addCustomFilter}>
                    Add Filter
                  </button>
                </div>
              )}

              <button
                className="primary-button"
                type="submit"
                disabled={!selectedReport || !activeProjectDbList.length || generating || downloading}
              >
                <Play size={18} />
                {generating
                  ? `Generating ${formatLabel(outputFormat)} report…`
                  : downloading
                    ? `Downloading ${formatLabel(outputFormat)} report…`
                    : 'Generate Report'}
              </button>
            </form>
          ) : null}

          {subTab === 'history' ? (
            <div className="surface">
              <div className="history-list">
                {history.length ? (
                  history.map((item) => (
                    <div className="history-item" key={`${item.output_file}-${item.createdAt}`}>
                      <div>
                        <strong>{item.reportName}</strong>
                        <span>{item.databaseName} · {item.createdAt}</span>
                        <code className="history-path">{displayOutputPath(item.output_file)}</code>
                      </div>
                      <button
                        className="secondary-button download-link"
                        type="button"
                        disabled={downloading}
                        onClick={() => onDownloadHistoryItem(item)}
                      >
                        <Download size={16} />
                        {downloading ? 'Downloading…' : `Download ${formatLabel(item.output_format || 'excel')}`}
                      </button>
                    </div>
                  ))
                ) : (
                  <div className="empty-state">Generated files will appear here</div>
                )}
              </div>
            </div>
          ) : null}
        </section>
      </section>

      <ConnectionsPanel
        activeDatabases={activeDatabases}
        databases={databases}
        open={connectionsOpen}
        primaryDatabase={primaryDatabase}
        setError={setError}
        onClose={() => setConnectionsOpen(false)}
        onUpdated={async (payload) => {
          await applyDatabasePayload(payload || await fetchDatabases(), { invalidateCaches: true });
          await loadReportsCatalog(project);
        }}
      />
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);
