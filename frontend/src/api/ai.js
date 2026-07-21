// api/ai.js — AI workflow API calls
// All POST to /api/ai/run/<workflow>
// Falls back to mock data on failure
import { api } from './index.js';
import { useStreaming } from '../composables/useStreaming.js';
import {
  MOCK_JD_RESULT,
  MOCK_SEARCH_RESULTS,
  MOCK_MATCH_RESULT,
  MOCK_INTERVIEW_QUESTIONS,
  MOCK_COMMUNICATION_DRAFT,
  MOCK_REPORT_RESULT,
} from '../data/ai.js';

// Export SSE streaming API (to be used with useStreaming composable)
export const STREAM_WORKFLOWS = {
  'jd-generate': '/api/ai/stream/jd-generate',
  'match': '/api/ai/stream/match',
};

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Wrap API call with mock fallback — simulate async for realistic UX
// Transient gateway errors (backend dev-server restart / cold start) get a few
// long-backoff retries before falling back to mock, so a brief 502 window does
// not silently swap real AI results for mock data.
const AI_RETRY_DELAYS = [3000, 6000];

function isTransientGatewayError(e) {
  return (e.status >= 500 && e.status < 600) || !e.status || e.code === 'NETWORK_ERROR' || e.code === 'TIMEOUT';
}

async function aiPost(workflow, params, mockData, mockDelay = 600) {
  let lastError = null;
  for (let attempt = 0; attempt <= AI_RETRY_DELAYS.length; attempt++) {
    try {
      // silent: AI workflows surface their own fallback UI, no global error toast
      const r = await api.post(`/ai/run/${workflow}`, params, { silent: true });
      const data = r.data || r;
      // Surface fallback warnings to the user
      if (data._fallback) {
        console.warn(`[AI API] ${workflow} returned fallback data:`, data._fallback_reason || 'unknown reason');
      }
      return data;
    } catch (e) {
      lastError = e;
      if (isTransientGatewayError(e) && attempt < AI_RETRY_DELAYS.length) {
        console.warn(`[AI API] ${workflow} transient error (${e.message}), retrying in ${AI_RETRY_DELAYS[attempt] / 1000}s...`);
        await delay(AI_RETRY_DELAYS[attempt]);
        continue;
      }
      break;
    }
  }
  console.warn(`[AI API] ${workflow} failed, using mock data:`, lastError.message);
  await delay(mockDelay);
  return { ...mockData, _fallback: true, _fallback_reason: lastError.message };
}

export async function runJdGenerate(params) {
  return aiPost('jd-generate', params, { ...MOCK_JD_RESULT, position: params.position || MOCK_JD_RESULT.position, department: params.department || MOCK_JD_RESULT.department });
}

export async function runResumeSearch(params) {
  return aiPost('resume-search', params, { results: MOCK_SEARCH_RESULTS });
}

export async function runMatch(params) {
  return aiPost('match', params, MOCK_MATCH_RESULT);
}

export async function runInterviewQuestions(params) {
  return aiPost('interview-questions', params, MOCK_INTERVIEW_QUESTIONS);
}

export async function runCommunicationDraft(params) {
  return aiPost('communication-draft', params, MOCK_COMMUNICATION_DRAFT);
}

export async function runReportAnalysis(params) {
  return aiPost('report-analysis', params, MOCK_REPORT_RESULT);
}
