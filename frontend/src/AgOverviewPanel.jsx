import React, { useEffect, useMemo, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { fetchAgOverview } from './api';

function formatCell(value) {
  if (value === null || value === undefined || value === '') return '—';
  return String(value);
}

function OverviewTable({ columns, rows, emptyLabel }) {
  if (!rows.length) {
    return <div className="empty-state compact">{emptyLabel}</div>;
  }

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {columns.map((column) => (
                <td key={column.key}>{formatCell(row[column.key])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const PROJECT_COLUMNS = [
  { key: 'country', label: 'Country' },
  { key: 'language', label: 'Language' },
  { key: 'language_iso_code', label: 'ISO Code' },
  { key: 'dialect', label: 'Dialect' },
  { key: 'project_name', label: 'Project' },
  { key: 'project_type', label: 'Type' },
  { key: 'project_stage', label: 'Stage' },
  { key: 'assigned_users', label: 'Assigned Users' },
];

const ASSIGNMENT_COLUMNS = [
  { key: 'country', label: 'Country' },
  { key: 'language', label: 'Language' },
  { key: 'language_iso_code', label: 'ISO Code' },
  { key: 'dialect', label: 'Dialect' },
  { key: 'project_name', label: 'Project' },
  { key: 'project_type', label: 'Type' },
  { key: 'project_stage', label: 'Stage' },
  { key: 'autographa_id', label: 'Autographa ID' },
  { key: 'user_name', label: 'User' },
  { key: 'assignment_role', label: 'Role' },
];

export default function AgOverviewPanel({ database, setError }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState('projects');
  const [filters, setFilters] = useState({
    country: '',
    language: '',
    project_type: '',
    dialect: '',
  });

  const filterKey = useMemo(() => JSON.stringify(filters), [filters]);

  async function loadOverview({ force = false } = {}) {
    if (!database) return;
    setLoading(true);
    setError('');
    try {
      const payload = await fetchAgOverview({
        database,
        country: filters.country || undefined,
        language: filters.language || undefined,
        project_type: filters.project_type || undefined,
        dialect: filters.dialect || undefined,
        refresh: force,
      });
      setData(payload);
    } catch (err) {
      setError(err.message);
      setData(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadOverview();
  }, [database, filterKey]);

  const summary = data?.summary || {};
  const options = data?.filter_options || {};

  return (
    <div className="surface ag-overview">
      <div className="section-heading">
        <div className="data-meta">
          <strong>AG Project Overview</strong>
          <span>{database || 'No database selected'}</span>
          {data?.cached ? <span>cached</span> : null}
          {loading ? <span>Loading…</span> : null}
        </div>
        <button
          className="secondary-button"
          type="button"
          disabled={loading || !database}
          onClick={() => loadOverview({ force: true })}
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      <div className="stats-grid compact overview-summary">
        <div className="metric"><span>Countries</span><strong>{summary.countries ?? '—'}</strong></div>
        <div className="metric"><span>Languages</span><strong>{summary.languages ?? '—'}</strong></div>
        <div className="metric"><span>Dialects</span><strong>{summary.dialects ?? '—'}</strong></div>
        <div className="metric"><span>Projects</span><strong>{summary.projects ?? '—'}</strong></div>
        <div className="metric"><span>Assignments</span><strong>{summary.assignments ?? '—'}</strong></div>
        <div className="metric"><span>Users Assigned</span><strong>{summary.users_assigned ?? '—'}</strong></div>
      </div>

      <div className="overview-filters">
        <label className="field">
          <span>Country</span>
          <select
            value={filters.country}
            onChange={(event) => setFilters((current) => ({ ...current, country: event.target.value }))}
          >
            <option value="">All countries</option>
            {(options.countries || []).map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Language</span>
          <select
            value={filters.language}
            onChange={(event) => setFilters((current) => ({ ...current, language: event.target.value }))}
          >
            <option value="">All languages</option>
            {(options.languages || []).map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Dialect</span>
          <select
            value={filters.dialect}
            onChange={(event) => setFilters((current) => ({ ...current, dialect: event.target.value }))}
          >
            <option value="">All dialects</option>
            {(options.dialects || []).map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Project type</span>
          <select
            value={filters.project_type}
            onChange={(event) => setFilters((current) => ({ ...current, project_type: event.target.value }))}
          >
            <option value="">All types</option>
            {(options.project_types || []).map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </label>
      </div>

      <div className="sheet-tabs overview-tabs">
        <button
          className={view === 'projects' ? 'sheet-tab active' : 'sheet-tab'}
          type="button"
          onClick={() => setView('projects')}
        >
          Projects ({data?.limits?.projects_total ?? 0})
        </button>
        <button
          className={view === 'assignments' ? 'sheet-tab active' : 'sheet-tab'}
          type="button"
          onClick={() => setView('assignments')}
        >
          User Assignments ({data?.limits?.assignments_total ?? 0})
        </button>
      </div>

      {view === 'projects' ? (
        <>
          <p className="overview-note">
            One row per project with country, language, ISO code, dialect, and assigned user count.
            Project progress metrics will be added here later.
          </p>
          <OverviewTable
            columns={PROJECT_COLUMNS}
            rows={data?.projects || []}
            emptyLabel={loading ? 'Loading projects…' : 'No projects found for the current filters'}
          />
        </>
      ) : (
        <>
          <p className="overview-note">
            One row per user assigned to a project, including country, language, ISO code, dialect, and role.
          </p>
          <OverviewTable
            columns={ASSIGNMENT_COLUMNS}
            rows={data?.assignments || []}
            emptyLabel={loading ? 'Loading assignments…' : 'No assignments found for the current filters'}
          />
        </>
      )}

      {data?.updated_at ? (
        <p className="overview-updated">Updated {data.updated_at}</p>
      ) : null}
    </div>
  );
}
