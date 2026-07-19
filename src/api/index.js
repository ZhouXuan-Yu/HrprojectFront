// api/index.js — HTTP client for backend API
const BASE = '/api';
const TIMEOUT_MS = 5000;

async function request(path, options = {}) {
  const url = `${BASE}${path}`;
  const headers = { 'Content-Type': 'application/json', ...options.headers };

  // Bearer token auth — set by login page on successful backend auth
  const token = localStorage.getItem('hr_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const config = {
    headers,
    ...options,
    signal: options.signal || AbortSignal.timeout(TIMEOUT_MS),
  };

  // In dev mode, forward the current role as query param for auth
  const role = localStorage.getItem('hr_role');
  if (role && !url.includes('role=')) {
    const sep = url.includes('?') ? '&' : '?';
    const urlWithRole = `${url}${sep}role=${role}`;
    const resp = await fetch(urlWithRole, config);
    return handleResponse(resp);
  }

  const resp = await fetch(url, config);
  return handleResponse(resp);
}

async function handleResponse(resp) {
  // 401 / 403 — clear stale token on real auth error (not missing token in dev mode)
  if ((resp.status === 401 || resp.status === 403) && localStorage.getItem('hr_token')) {
    localStorage.removeItem('hr_token');
    const err = new Error('请重新登录');
    err.code = 'UNAUTHORIZED';
    err.status = resp.status;
    throw err;
  }
  const json = await resp.json();
  if (!resp.ok) {
    const err = new Error(json?.error?.message || json?.message || '请求失败');
    err.code = json?.error?.code || 'ERROR';
    err.status = resp.status;
    // Dispatch global event for toast notification
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('api:error', {
        detail: { message: err.message, code: err.code, status: err.status },
      }));
    }
    throw err;
  }
  return json;
}

export const api = {
  get: (path) => request(path),
  post: (path, data) => request(path, { method: 'POST', body: JSON.stringify(data) }),
  patch: (path, data) => request(path, { method: 'PATCH', body: JSON.stringify(data) }),
  put: (path, data) => request(path, { method: 'PUT', body: JSON.stringify(data) }),
};
