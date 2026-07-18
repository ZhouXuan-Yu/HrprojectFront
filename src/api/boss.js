// api/boss.js — BOSS直聘 integration API (boss-cli wrapper)
import { api } from './index.js';

// Helper: wrap API call with {ok, data} / {ok: false, error} contract
async function safeCall(fn) {
  try {
    const data = await fn();
    return { ok: true, data };
  } catch (e) {
    return { ok: false, error: e.message || '请求失败' };
  }
}

// Status & connection
export function fetchBossStatus() {
  return safeCall(() => api.get('/boss/status'));
}

// Positions
export function fetchPositions() {
  return safeCall(() => api.get('/boss/positions'));
}

export function fetchPositionDetail(name) {
  return safeCall(() => api.get(`/boss/positions/${encodeURIComponent(name)}`));
}

// Candidate search
export function searchCandidates(params = {}) {
  return safeCall(() => api.post('/boss/candidates/search', params));
}

// Chat list
export function fetchChatList(unreadOnly = false) {
  const query = unreadOnly ? '?unread=1' : '';
  return safeCall(() => api.get(`/boss/chat/list${query}`));
}

// Chat operations
export function openChat(name, index) {
  return safeCall(() => api.post('/boss/chat/open', { name, index }));
}

export function sendMessage(text, requestResume = false) {
  return safeCall(() => api.post('/boss/chat/send', { text, request_resume: requestResume }));
}

// Actions
export function bossAction(action, remark) {
  return safeCall(() => api.post('/boss/action', { action, remark }));
}

export function previewResume(name) {
  return safeCall(() => api.post('/boss/resume/preview', { name }));
}

export function greetCandidate(name, job) {
  return safeCall(() => api.post('/boss/greet', { name, job }));
}
