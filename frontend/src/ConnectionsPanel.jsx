import React, { useMemo, useState } from 'react';
import { Check, Plus, Server, Trash2, X } from 'lucide-react';
import {
  createDatabaseConnection,
  deleteDatabaseConnection,
  testDatabaseConnection,
  updateActiveDatabases,
  updateDatabaseConnection,
} from './api';

const EMPTY_FORM = {
  name: '',
  host: '',
  port: '5432',
  database: '',
  user: '',
  password: '',
  ssl_mode: 'prefer',
  description: '',
  environment: 'production',
  project: 'AG',
  category: 'AG',
  active: true,
};

const PROJECT_OPTIONS = ['AG', 'LMS', 'Telios', 'Language', 'Utility'];

export default function ConnectionsPanel({
  open,
  databases,
  activeDatabases,
  primaryDatabase,
  onClose,
  onUpdated,
  setError,
}) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [editingName, setEditingName] = useState('');
  const [busy, setBusy] = useState('');
  const [showForm, setShowForm] = useState(false);

  const activeSet = useMemo(() => new Set(activeDatabases), [activeDatabases]);

  function resetForm() {
    setForm(EMPTY_FORM);
    setEditingName('');
    setShowForm(false);
  }

  function startEdit(connection) {
    setEditingName(connection.name);
    setForm({
      name: connection.name,
      host: connection.host,
      port: String(connection.port || 5432),
      database: connection.database,
      user: connection.user,
      password: '',
      ssl_mode: connection.ssl_mode || 'prefer',
      description: connection.description || '',
      environment: connection.environment || 'production',
      project: connection.project || connection.category || 'AG',
      category: connection.category || connection.project || 'AG',
      active: activeSet.has(connection.name),
    });
    setShowForm(true);
  }

  async function toggleActive(name) {
    const next = activeSet.has(name)
      ? activeDatabases.filter((item) => item !== name)
      : [...activeDatabases, name];

    if (!next.length) {
      setError('At least one database must remain active');
      return;
    }

    setBusy(`active-${name}`);
    setError('');
    try {
      await onUpdated(await updateActiveDatabases(next, primaryDatabase === name && !next.includes(name) ? next[0] : primaryDatabase));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy('');
    }
  }

  async function setPrimary(name) {
    if (!activeSet.has(name)) return;
    setBusy(`primary-${name}`);
    setError('');
    try {
      await onUpdated(await updateActiveDatabases(activeDatabases, name));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy('');
    }
  }

  async function handleTest() {
    setBusy('test');
    setError('');
    try {
      await testDatabaseConnection({
        host: form.host,
        port: Number(form.port),
        database: form.database,
        user: form.user,
        password: form.password,
        ssl_mode: form.ssl_mode || undefined,
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy('');
    }
  }

  async function handleSave(event) {
    event.preventDefault();
    setBusy('save');
    setError('');
    try {
      const payload = {
        ...form,
        port: Number(form.port),
        category: form.category || form.project,
      };

      if (editingName) {
        await updateDatabaseConnection(editingName, payload);
      } else {
        await createDatabaseConnection(payload);
      }

      const nextActive = payload.active && !activeSet.has(form.name)
        ? [...activeDatabases, form.name]
        : activeDatabases;
      const response = await updateActiveDatabases(nextActive, primaryDatabase || form.name);
      await onUpdated(response);
      resetForm();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy('');
    }
  }

  async function handleDelete(name) {
    if (!window.confirm(`Delete connection "${name}"?`)) return;
    setBusy(`delete-${name}`);
    setError('');
    try {
      await deleteDatabaseConnection(name);
      await onUpdated();
      if (editingName === name) resetForm();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy('');
    }
  }

  if (!open) return null;

  return (
    <div className="connections-overlay" role="presentation" onClick={onClose}>
      <aside className="connections-panel" onClick={(event) => event.stopPropagation()} aria-label="Database connections">
        <header className="connections-header">
          <div>
            <p className="eyebrow">Connections</p>
            <h2>Database Connections</h2>
          </div>
          <button className="icon-button" type="button" onClick={onClose} title="Close">
            <X size={18} />
          </button>
        </header>

        <p className="connections-help">
          Check the databases you want active. Reports and previews use all active connections for the current project.
        </p>

        <div className="connections-list">
          {databases.map((connection) => (
            <div className={`connection-item${activeSet.has(connection.name) ? ' active' : ''}`} key={connection.name}>
              <label className="connection-check">
                <input
                  checked={activeSet.has(connection.name)}
                  disabled={busy === `active-${connection.name}`}
                  type="checkbox"
                  onChange={() => toggleActive(connection.name)}
                />
                <span>{connection.name}</span>
              </label>
              <div className="connection-meta">
                <span>{connection.host}:{connection.port}</span>
                <span>{connection.category || connection.project}</span>
                <span>{connection.environment}</span>
              </div>
              <div className="connection-actions">
                <button
                  className={primaryDatabase === connection.name ? 'secondary-button active-pill' : 'secondary-button'}
                  disabled={!activeSet.has(connection.name) || busy === `primary-${connection.name}`}
                  type="button"
                  onClick={() => setPrimary(connection.name)}
                >
                  {primaryDatabase === connection.name ? 'Primary' : 'Set primary'}
                </button>
                {connection.is_custom ? (
                  <>
                    <button className="secondary-button" type="button" onClick={() => startEdit(connection)}>
                      Edit
                    </button>
                    <button
                      className="secondary-button danger"
                      disabled={busy === `delete-${connection.name}`}
                      type="button"
                      onClick={() => handleDelete(connection.name)}
                    >
                      <Trash2 size={14} />
                    </button>
                  </>
                ) : (
                  <span className="connection-badge">Built-in</span>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="connections-form-wrap">
          {showForm ? (
            <form className="connections-form" onSubmit={handleSave}>
              <h3>{editingName ? `Edit ${editingName}` : 'Add Connection'}</h3>
              <div className="form-grid">
                <label className="field">
                  <span>Name</span>
                  <input
                    disabled={Boolean(editingName)}
                    required
                    value={form.name}
                    onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                  />
                </label>
                <label className="field">
                  <span>Host</span>
                  <input
                    required
                    value={form.host}
                    onChange={(event) => setForm((current) => ({ ...current, host: event.target.value }))}
                  />
                </label>
                <label className="field">
                  <span>Port</span>
                  <input
                    required
                    value={form.port}
                    onChange={(event) => setForm((current) => ({ ...current, port: event.target.value }))}
                  />
                </label>
                <label className="field">
                  <span>Database</span>
                  <input
                    required
                    value={form.database}
                    onChange={(event) => setForm((current) => ({ ...current, database: event.target.value }))}
                  />
                </label>
                <label className="field">
                  <span>User</span>
                  <input
                    required
                    value={form.user}
                    onChange={(event) => setForm((current) => ({ ...current, user: event.target.value }))}
                  />
                </label>
                <label className="field">
                  <span>Password</span>
                  <input
                    type="password"
                    value={form.password}
                    onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
                    placeholder={editingName ? 'Leave blank to keep current password' : ''}
                  />
                </label>
                <label className="field">
                  <span>Project</span>
                  <select
                    value={form.project}
                    onChange={(event) => setForm((current) => ({
                      ...current,
                      project: event.target.value,
                      category: event.target.value,
                    }))}
                  >
                    {PROJECT_OPTIONS.map((item) => (
                      <option key={item} value={item}>{item}</option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  <span>SSL Mode</span>
                  <select
                    value={form.ssl_mode}
                    onChange={(event) => setForm((current) => ({ ...current, ssl_mode: event.target.value }))}
                  >
                    <option value="disable">disable</option>
                    <option value="prefer">prefer</option>
                    <option value="require">require</option>
                  </select>
                </label>
                <label className="field field-wide">
                  <span>Description</span>
                  <input
                    value={form.description}
                    onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
                  />
                </label>
              </div>
              <label className="toggle">
                <input
                  checked={form.active}
                  type="checkbox"
                  onChange={(event) => setForm((current) => ({ ...current, active: event.target.checked }))}
                />
                Activate after saving
              </label>
              <div className="connections-form-actions">
                <button className="secondary-button" disabled={busy === 'test'} type="button" onClick={handleTest}>
                  <Server size={16} />
                  {busy === 'test' ? 'Testing' : 'Test'}
                </button>
                <button className="secondary-button" type="button" onClick={resetForm}>Cancel</button>
                <button className="primary-button" disabled={busy === 'save'} type="submit">
                  <Check size={16} />
                  {busy === 'save' ? 'Saving' : 'Save'}
                </button>
              </div>
            </form>
          ) : (
            <button className="primary-button connections-add" type="button" onClick={() => setShowForm(true)}>
              <Plus size={18} />
              Add Connection
            </button>
          )}
        </div>
      </aside>
    </div>
  );
}
