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
