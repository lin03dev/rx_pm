const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

async function request(path, options) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
    ...options,
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || `Request failed with ${response.status}`);
  }
  return payload;
}

export function fetchReports() {
  return request('/api/reports');
}

export function fetchDatabases() {
  return request('/api/databases');
}

export function updateActiveDatabases(active, primary) {
  return request('/api/databases/active', {
    method: 'PUT',
    body: JSON.stringify({ active, primary }),
  });
}

export function updateDatabaseSelection(project, database) {
  return request('/api/databases/selection', {
    method: 'PUT',
    body: JSON.stringify({ project, database }),
  });
}

export function testDatabaseConnection(body) {
  return request('/api/databases/test', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function createDatabaseConnection(body) {
  return request('/api/databases', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function updateDatabaseConnection(name, body) {
  return request(`/api/databases/${encodeURIComponent(name)}`, {
    method: 'PUT',
    body: JSON.stringify(body),
  });
}

export function deleteDatabaseConnection(name) {
  return request(`/api/databases/${encodeURIComponent(name)}`, {
    method: 'DELETE',
  });
}

export function fetchDashboardInsights(project, database, refresh = false) {
  const params = new URLSearchParams({ project, database, refresh: String(refresh) });
  return request(`/api/dashboard/insights?${params.toString()}`);
}

export function fetchReportPreview(body) {
  return request('/api/reports/preview', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function generateReport(body) {
  return request('/api/reports/generate', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function fileDownloadUrl(path) {
  const params = new URLSearchParams({ path });
  return `${API_BASE}/api/files?${params.toString()}`;
}

export async function downloadReportFile(outputPath) {
  const url = fileDownloadUrl(outputPath);
  const response = await fetch(url);
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || `Download failed with ${response.status}`);
  }

  const blob = await response.blob();
  const filename = outputPath.split(/[/\\]/).pop() || 'report.xlsx';
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = objectUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(objectUrl);
  return filename;
}
