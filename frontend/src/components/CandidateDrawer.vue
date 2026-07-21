<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-overlay" @click.self="close">
      <div class="modal-box candidate-drawer" role="dialog" aria-modal="true" aria-label="候选人画像">
        <div class="drawer-header">
          <div class="drawer-header-left">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--c-primary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            <h3>{{ data.name || '加载中...' }}</h3>
          </div>
          <button class="drawer-close" @click="close" aria-label="关闭">✕</button>
        </div>

        <div v-if="loading" class="drawer-body" style="text-align:center;padding:40px">
          <div style="color:var(--c-sub);font-size:14px">加载中...</div>
        </div>

        <div v-else-if="errorMsg" class="drawer-body" style="text-align:center;padding:40px">
          <div style="color:var(--c-reject);font-size:14px;margin-bottom:12px">{{ errorMsg }}</div>
          <button class="btn btn-outline btn-sm" @click="load">重试</button>
        </div>

        <div v-else class="drawer-body">
          <!-- Fallback banner -->
          <div v-if="data._fallback" class="mock-banner-sm">
            <span>ⓘ 当前为演示数据</span>
          </div>

          <div class="profile-grid">
            <div class="pf-item"><span class="pf-label">编号</span><span class="pf-value">{{ data.id }}</span></div>
            <div class="pf-item"><span class="pf-label">画像评分</span><span class="pf-value"><span class="portrait-score" :class="data.portraitClass">{{ data.portrait }}</span></span></div>
            <div class="pf-item"><span class="pf-label">学历</span><span class="pf-value">{{ data.edu }} · {{ data.schoolLevel }}</span></div>
            <div class="pf-item"><span class="pf-label">工作年限</span><span class="pf-value">{{ data.years }}</span></div>
            <div class="pf-item"><span class="pf-label">最近公司</span><span class="pf-value">{{ data.company }}</span></div>
            <div class="pf-item"><span class="pf-label">来源渠道</span><span class="pf-value">{{ data.source }}</span></div>
            <div class="pf-item"><span class="pf-label">入库时间</span><span class="pf-value">{{ data.inDate }}</span></div>
            <div class="pf-item"><span class="pf-label">手机</span><span class="pf-value">{{ data.mobile }}</span></div>
            <div class="pf-item"><span class="pf-label">邮箱</span><span class="pf-value">{{ data.email }}</span></div>
            <div class="pf-item"><span class="pf-label">状态</span><span class="pf-value"><StatusBadge :type="data.status === 'available' ? 'done' : (data.status === 'locked' ? 'progress' : 'draft')">{{ data.statusLabel }}</StatusBadge></span></div>
            <div v-if="data.blackFlag" class="pf-item" style="grid-column: span 2"><span class="pf-label">黑名单</span><span class="pf-value" style="color:var(--c-reject)">⚠ 已标记黑名单</span></div>
          </div>

          <div v-if="data.skills && data.skills.length" style="margin-top:16px">
            <div style="font-size:13px;font-weight:700;color:var(--c-text);margin-bottom:8px">核心技能</div>
            <div style="display:flex;flex-wrap:wrap;gap:6px">
              <span v-for="sk in data.skills" :key="sk" class="tag-item tag-hit">{{ sk }}</span>
            </div>
          </div>

          <div v-if="data.note" style="margin-top:16px;padding:12px;background:var(--c-bg);border-radius:8px;font-size:13px;color:var(--c-body)">
            <span style="font-weight:700;color:var(--c-text)">备注：</span>{{ data.note }}
          </div>

          <!-- AI 简历解析结果 -->
          <div v-if="data.resume" style="margin-top:16px;padding:14px;background:var(--c-primary-subtle,#EEF2FF);border:1px solid rgba(79,110,247,.18);border-radius:10px">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
              <div style="font-size:13px;font-weight:700;color:var(--c-text)">
                🤖 AI 简历解析
                <span style="font-size:11px;font-weight:400;color:var(--c-sub);margin-left:6px">
                  {{ data.resume.parseEngine === 'deepseek' ? 'DeepSeek' : '本地解析' }} · {{ data.resume.parsedAt }}
                </span>
              </div>
              <button v-if="data.resume.resumeId && data.resume.fileName" class="btn btn-outline btn-sm"
                      :disabled="openingFile" @click="openResumeFile">
                {{ openingFile ? '打开中...' : '📄 查看原件' }}
              </button>
            </div>
            <div v-if="data.resume.summary" style="font-size:13px;color:var(--c-body);line-height:1.7;margin-bottom:10px">{{ data.resume.summary }}</div>
            <div v-if="data.resume.skills && data.resume.skills.length" style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px">
              <span v-for="sk in data.resume.skills" :key="sk" class="tag-item tag-hit">{{ sk }}</span>
            </div>
            <div v-if="data.resume.certs && data.resume.certs.length" style="font-size:12px;color:var(--c-sub)">
              证书：{{ data.resume.certs.join('、') }}
            </div>
            <div style="font-size:11px;color:var(--c-sub);margin-top:8px">
              原件：{{ data.resume.fileName || '(未保存文件)' }} · 入库 {{ data.resume.storageTime }}
            </div>
          </div>
        </div>

        <div class="drawer-actions" v-if="!loading && !errorMsg">
          <button v-if="data.status === 'available'" class="btn btn-outline btn-sm" @click="$emit('contact', data)">联系</button>
          <button v-if="data.status === 'available'" class="btn btn-primary btn-sm" @click="$emit('join', data)">加入需求</button>
          <button class="btn btn-ghost btn-sm" @click="close">关闭</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue';
import { fetchCandidateDetail, fetchResumeFile } from '../api/talent.js';

const props = defineProps({
  visible: { type: Boolean, default: false },
  candidateId: { type: String, default: '' },
});

const emit = defineEmits(['close', 'contact', 'join']);

const data = ref({});
const loading = ref(false);
const errorMsg = ref('');
const openingFile = ref(false);

watch(() => [props.visible, props.candidateId], ([v]) => { if (v) load(); }, { immediate: true });

async function load() {
  if (!props.candidateId) return;
  loading.value = true;
  errorMsg.value = '';
  try {
    const result = await fetchCandidateDetail(props.candidateId);
    data.value = result;
  } catch (e) {
    errorMsg.value = e.message || '加载候选人详情失败';
  } finally {
    loading.value = false;
  }
}

async function openResumeFile() {
  const resumeId = data.value?.resume?.resumeId;
  if (!resumeId) return;
  openingFile.value = true;
  try {
    const blob = await fetchResumeFile(resumeId);
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank');
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  } catch (e) {
    errorMsg.value = '打开简历原件失败：' + (e.message || '未知错误');
  } finally {
    openingFile.value = false;
  }
}

function close() { emit('close'); }
</script>

<style scoped>
.modal-overlay { position: fixed; inset: 0; background: rgba(15,23,42,0.38); backdrop-filter: blur(2px); z-index: 300; display: flex; align-items: center; justify-content: center; }
.candidate-drawer { width: 540px; max-width: 92vw; max-height: 85vh; display: flex; flex-direction: column; border-radius: 10px; border: 1px solid var(--e-border, #E1E6EF); background: var(--e-surface, #FFFFFF); box-shadow: 0 24px 80px rgba(15,23,42,0.2); }
.drawer-header { display: flex; align-items: center; justify-content: space-between; padding: 14px 20px; border-bottom: 1px solid var(--e-border-soft, #EFF3F8); }
.drawer-header-left { display: flex; align-items: center; gap: 8px; color: var(--c-primary); }
.drawer-header-left h3 { font-size: 16px; font-weight: 700; color: var(--c-text); margin: 0; }
.drawer-close { width: 32px; height: 32px; border-radius: 50%; border: none; background: var(--e-surface-soft, #F2F5FA); color: var(--c-sub); cursor: pointer; font-size: 16px; display: flex; align-items: center; justify-content: center; }
.drawer-close:hover { background: var(--c-border); }
.drawer-body { flex: 1; overflow-y: auto; padding: 16px 20px; }
.profile-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 24px; }
.pf-item { display: flex; flex-direction: column; gap: 2px; }
.pf-label { font-size: 11px; color: var(--c-sub); font-weight: 600; }
.pf-value { font-size: 13px; color: var(--c-text); font-weight: 600; }
.drawer-actions { display: flex; gap: 8px; justify-content: flex-end; padding: 12px 20px; border-top: 1px solid var(--e-border-soft, #EFF3F8); }
.mock-banner-sm { padding: 6px 12px; background: #FFF8E1; border: 1px solid #FFE082; border-radius: 6px; font-size: 12px; color: #795548; margin-bottom: 12px; }
.btn { display: inline-flex; align-items: center; gap: 5px; padding: 6px 14px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: var(--c-primary); color: #fff; }
.btn-outline { background: transparent; border: 1px solid var(--c-border); color: var(--c-body); }
.btn-ghost { background: transparent; border: none; color: var(--c-sub); }
</style>
