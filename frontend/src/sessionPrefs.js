const STORAGE_KEY = 'rxpm.dashboard';

const DEFAULT_PREFS = {
  project: '',
  reportByProject: {},
};

export function loadDashboardPrefs() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...DEFAULT_PREFS };
    const parsed = JSON.parse(raw);
    return {
      project: typeof parsed.project === 'string' ? parsed.project : '',
      reportByProject: parsed.reportByProject && typeof parsed.reportByProject === 'object'
        ? parsed.reportByProject
        : {},
    };
  } catch {
    return { ...DEFAULT_PREFS };
  }
}

export function saveDashboardPrefs(prefs) {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify({
      project: prefs.project || '',
      reportByProject: prefs.reportByProject || {},
    }));
  } catch {
    // Ignore storage failures (private mode, quota, etc.)
  }
}

export function rememberReportSelection(project, reportId) {
  if (!project || !reportId) return;
  const prefs = loadDashboardPrefs();
  saveDashboardPrefs({
    ...prefs,
    project,
    reportByProject: {
      ...prefs.reportByProject,
      [project]: reportId,
    },
  });
}

export function rememberProjectSelection(project) {
  if (!project) return;
  const prefs = loadDashboardPrefs();
  saveDashboardPrefs({ ...prefs, project });
}
