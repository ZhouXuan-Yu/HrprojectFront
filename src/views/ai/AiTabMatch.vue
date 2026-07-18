<template>
  <div data-slot="ai-workspace">
    <div data-slot="ai-conversation">
      <AiChatMessage role="ai" status="complete">
        <p>选择候选人和岗位，系统会基于简历画像和岗位 JD 进行多维匹配打分，并给出详细理由。</p>
      </AiChatMessage>
      <AiChatMessage v-if="matchLoading && !matchStreamContent" role="ai" status="loading" />

      <!-- Streaming content during match -->
      <AiChatMessage
        v-if="matchLoading && matchStreamContent"
        role="ai"
        status="streaming"
        :streamingContent="matchStreamContent"
      />

      <AiChatMessage v-if="matchError && !matchLoading" role="ai" status="error">
        <template #error>{{ matchError }}</template>
      </AiChatMessage>
      <template v-if="matchResult && !matchLoading">
        <AiChatMessage role="ai" status="complete">
          <div data-slot="ai-match-result">
            <div data-slot="ai-match-score-row">
              <div data-slot="ai-match-big-score">
                <span data-slot="ai-match-score-num">{{ matchResult.overall_score }}</span>
                <span data-slot="ai-match-score-label">综合匹配得分</span>
              </div>
              <div data-slot="ai-match-breakdown">
                <div data-slot="ai-match-item"><span data-slot="ai-match-item-label">画像分</span><div class="progress-bar"><div class="progress-fill" :style="{ width: matchResult.profile_score + '%' }"></div></div><span data-slot="ai-match-item-val">{{ matchResult.profile_score }}</span></div>
                <div data-slot="ai-match-item"><span data-slot="ai-match-item-label">匹配分</span><div class="progress-bar"><div class="progress-fill" :style="{ width: matchResult.match_score + '%' }"></div></div><span data-slot="ai-match-item-val">{{ matchResult.match_score }}</span></div>
                <div data-slot="ai-match-item"><span data-slot="ai-match-item-label">综合等级</span><StatusBadge :type="matchResult.grade === 'A' ? 'done' : matchResult.grade === 'B' ? 'progress' : 'warn'">{{ matchResult.grade }} 级</StatusBadge></div>
              </div>
            </div>
            <div data-slot="ai-jd-section"><div data-slot="ai-jd-section-title">匹配优势</div><ul data-slot="ai-jd-list"><li v-for="(s, i) in matchResult.strengths" :key="'s'+i">{{ s }}</li></ul></div>
            <div v-if="matchResult.missing_skills?.length" data-slot="ai-jd-section"><div data-slot="ai-jd-section-title">待补足技能</div><div data-slot="ai-jd-skill-table"><div v-for="ms in matchResult.missing_skills" :key="ms.skill" data-slot="ai-jd-skill-row"><span data-slot="ai-jd-skill-name">{{ ms.skill }}</span><StatusBadge :type="ms.importance === '加分项' ? 'draft' : 'warn'">{{ ms.importance }}</StatusBadge><span data-slot="ai-jd-skill-desc">{{ ms.note }}</span></div></div></div>
            <div data-slot="ai-jd-section"><div data-slot="ai-jd-section-title">详细理由</div><ul data-slot="ai-jd-list"><li v-for="(r, i) in matchResult.reasons" :key="'mr'+i">{{ r }}</li></ul></div>
          </div>
        </AiChatMessage>
        <AiDisclaimer />
      </template>
    </div>
    <div data-slot="ai-input-area">
      <div style="display:flex;gap:8px;margin-bottom:8px">
        <select v-model="matchForm.candidateId" style="flex:1;padding:7px 10px;border:1px solid var(--c-border);border-radius:var(--radius-sm);font-size:13px;font-family:inherit;background:var(--c-card);color:var(--c-body)" aria-label="选择候选人">
          <option value="">选择候选人</option>
          <option v-for="c in candidates" :key="c.id" :value="c.id">{{ c.name }} — {{ c.title }}</option>
        </select>
        <select v-model="matchForm.demandId" style="flex:1;padding:7px 10px;border:1px solid var(--c-border);border-radius:var(--radius-sm);font-size:13px;font-family:inherit;background:var(--c-card);color:var(--c-body)" aria-label="选择岗位">
          <option value="">选择岗位</option>
          <option v-for="d in demands" :key="d.id" :value="d.id">{{ d.name }} · {{ d.dept }}</option>
        </select>
      </div>
      <button class="btn btn-primary" style="width:100%" :disabled="!matchForm.candidateId || !matchForm.demandId || matchLoading" @click="runMatch">
        <AiSkeleton v-if="matchLoading" variant="spinner" />
        {{ matchLoading ? '匹配中...' : '开始匹配' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, inject } from 'vue';
import AiChatMessage from '../../components/ai/AiChatMessage.vue';
import AiSkeleton from '../../components/ai/AiSkeleton.vue';
import AiDisclaimer from '../../components/ai/AiDisclaimer.vue';
import StatusBadge from '../../components/StatusBadge.vue';
import { runMatch as apiRunMatch } from '../../api/ai.js';
import { useStreaming } from '../../composables/useStreaming.js';

const showToast = inject('showToast');
const candidates = inject('aiCandidates');
const demands = inject('aiDemands');

// Streaming (SSE) for match
const {
  content: matchStreamContent,
  thinking: matchThinking,
  isStreaming: matchStreaming,
  error: matchStreamError,
  result: matchStreamResult,
  start: startMatchStream,
  stop: stopMatchStream,
} = useStreaming();

const matchForm = reactive({ candidateId: '', demandId: '' });
const matchResult = ref(null);
const matchLoading = ref(false);
const matchError = ref('');

// Watch for match streaming completion
watch([matchStreamContent, matchStreamResult, matchStreamError], () => {
  if (matchStreamError.value) {
    matchError.value = matchStreamError.value;
    matchLoading.value = false;
  }
  if (!matchStreaming.value && matchStreamContent.value) {
    matchResult.value = {
      overall_score: matchStreamResult.value?.overall_score ?? 0,
      profile_score: matchStreamResult.value?.profile_score ?? 0,
      match_score: matchStreamResult.value?.match_score ?? 0,
      grade: matchStreamResult.value?.grade ?? 'B',
      reasons: matchStreamResult.value?.reasons || ['流式生成内容，请查看上方信息'],
      missing_skills: matchStreamResult.value?.missing_skills || [],
      strengths: matchStreamResult.value?.strengths || [],
      disclaimer: matchStreamResult.value?.disclaimer || '此内容由AI生成，请人工审核确认后使用',
    };
    matchLoading.value = false;
  }
});

async function runMatch() {
  if (!matchForm.candidateId || !matchForm.demandId) return;
  matchError.value = ''; matchLoading.value = true;
  try {
    await startMatchStream('match', { candidate_id: matchForm.candidateId, demand_id: matchForm.demandId });
    showToast('匹配完成');
  } catch (e) {
    // Fallback to blocking API
    matchLoading.value = true;
    try {
      matchResult.value = await apiRunMatch({ candidate_id: matchForm.candidateId, demand_id: matchForm.demandId });
      showToast('匹配完成');
    } catch (e2) {
      matchError.value = e2.message || '匹配失败，请重试';
      showToast(matchError.value);
    }
    matchLoading.value = false;
  }
}
</script>

<style scoped>
/* ===== AI Workspace layout ===== */
[data-slot="ai-workspace"] {
  display: flex;
  flex-direction: column;
  min-height: 420px;
  max-height: calc(100vh - 280px);
}
[data-slot="ai-conversation"] {
  flex: 1;
  overflow-y: auto;
  padding: 0 4px;
}
[data-slot="ai-input-area"] {
  padding-top: 12px;
  border-top: 1px solid var(--c-border-light);
  flex-shrink: 0;
}

/* ===== JD Result shared sections (used by match too) ===== */
[data-slot="ai-jd-section"] { margin-bottom:16px }
[data-slot="ai-jd-section-title"] { font-size:12px;font-weight:700;color:var(--c-text);margin-bottom:8px;display:flex;align-items:center;gap:6px }
[data-slot="ai-jd-section-title"]::before { content:'';width:3px;height:12px;background:var(--c-primary);border-radius:2px }
[data-slot="ai-jd-list"] { padding-left:16px;font-size:13px;color:var(--c-body);line-height:2 }
[data-slot="ai-jd-skill-table"] { border:1px solid var(--c-border);border-radius:var(--radius-sm);overflow:hidden }
[data-slot="ai-jd-skill-row"] { display:flex;align-items:center;gap:8px;padding:8px 12px;border-bottom:1px solid var(--c-border-light);font-size:12px }
[data-slot="ai-jd-skill-row"]:last-child { border-bottom:none }
[data-slot="ai-jd-skill-name"] { font-weight:600;color:var(--c-text);min-width:70px }
[data-slot="ai-jd-skill-desc"] { color:var(--c-sub);flex:1 }

/* ===== Match result ===== */
[data-slot="ai-match-result"] { font-size:13px }
[data-slot="ai-match-score-row"] { display:flex;gap:24px;align-items:flex-start;margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid var(--c-border) }
[data-slot="ai-match-big-score"] { text-align:center;min-width:100px }
[data-slot="ai-match-score-num"] { display:block;font-size:42px;font-weight:900;color:var(--c-primary);font-variant-numeric:tabular-nums;line-height:1 }
[data-slot="ai-match-score-label"] { font-size:11px;color:var(--c-sub);margin-top:2px;display:block }
[data-slot="ai-match-breakdown"] { flex:1 }
[data-slot="ai-match-item"] { display:flex;align-items:center;gap:10px;margin-bottom:8px;font-size:12px }
[data-slot="ai-match-item-label"] { color:var(--c-sub);min-width:48px }
[data-slot="ai-match-item-val"] { font-weight:700;color:var(--c-text);font-variant-numeric:tabular-nums;min-width:24px }

.progress-bar { flex:1;height:8px;background:var(--c-border-light);border-radius:4px;overflow:hidden }
.progress-fill { height:100%;background:var(--c-primary);border-radius:4px;transition:width .6s ease }

@media (prefers-reduced-motion: reduce) {
  .progress-fill { transition: none; }
}

/* Focus visible */
input:focus-visible, select:focus-visible { outline:2px solid var(--c-primary);outline-offset:1px }

/* ===== Mobile (≤768px) ===== */
@media (max-width: 768px) {
  [data-slot="ai-match-score-row"] {
    flex-direction: column;
    gap: 16px;
    align-items: center;
  }
  [data-slot="ai-match-big-score"] {
    min-width: auto;
  }
  [data-slot="ai-match-score-num"] {
    font-size: 36px;
  }
  [data-slot="ai-match-breakdown"] {
    width: 100%;
  }
}
</style>
