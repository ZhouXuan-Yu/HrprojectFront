<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-overlay" @click.self="close">
      <div class="modal-box employee-drawer" role="dialog" aria-modal="true" aria-label="员工信息">
        <div class="drawer-header">
          <div class="drawer-header-left">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--c-primary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
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
          <div v-if="data._fallback" class="mock-banner-sm">
            <span>ⓘ 当前为演示数据</span>
          </div>

          <div class="profile-grid">
            <div class="pf-item"><span class="pf-label">工号</span><span class="pf-value">{{ data.id }}</span></div>
            <div class="pf-item"><span class="pf-label">综合评估</span><span class="pf-value"><span class="portrait-score" :class="gradeClass">{{ data.grade }} · {{ data.score }}</span></span></div>
            <div class="pf-item"><span class="pf-label">部门</span><span class="pf-value">{{ data.dept }}</span></div>
            <div class="pf-item"><span class="pf-label">岗位</span><span class="pf-value">{{ data.pos }}</span></div>
            <div class="pf-item"><span class="pf-label">工龄</span><span class="pf-value">{{ data.years }}</span></div>
            <div class="pf-item"><span class="pf-label">绩效</span><span class="pf-value" style="color:var(--c-done);font-weight:700">{{ data.perf }}</span></div>
            <div class="pf-item"><span class="pf-label">可调岗</span><span class="pf-value"><StatusBadge :type="data.transfer ? 'done' : 'warn'">{{ data.transfer ? '可调' : '不可调' }}</StatusBadge></span></div>
            <div class="pf-item"><span class="pf-label">最近晋升</span><span class="pf-value">{{ data.lastPromote }}</span></div>
            <div v-if="data.restrictReason" class="pf-item" style="grid-column: span 2"><span class="pf-label">限制原因</span><span class="pf-value" style="color:var(--c-reject)">{{ data.restrictReason }}</span></div>
          </div>
        </div>

        <div class="drawer-actions" v-if="!loading && !errorMsg">
          <button v-if="data.transfer" class="btn btn-primary btn-sm" @click="$emit('interview', data)">发起内部面试</button>
          <button class="btn btn-ghost btn-sm" @click="close">关闭</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { fetchEmployeeDetail } from '../api/talent.js';

const props = defineProps({
  visible: { type: Boolean, default: false },
  employeeId: { type: String, default: '' },
});

const emit = defineEmits(['close', 'interview']);

const data = ref({});
const loading = ref(false);
const errorMsg = ref('');

const gradeClass = computed(() => {
  const s = data.value.score || 0;
  return s >= 80 ? 'score-high' : s >= 60 ? 'score-mid' : 'score-low';
});

watch(() => [props.visible, props.employeeId], ([v]) => { if (v) load(); });

async function load() {
  if (!props.employeeId) return;
  loading.value = true;
  errorMsg.value = '';
  try {
    const result = await fetchEmployeeDetail(props.employeeId);
    data.value = result;
  } catch (e) {
    errorMsg.value = e.message || '加载员工信息失败';
  } finally {
    loading.value = false;
  }
}

function close() { emit('close'); }
</script>

<style scoped>
.modal-overlay { position: fixed; inset: 0; background: rgba(15,23,42,0.38); backdrop-filter: blur(2px); z-index: 300; display: flex; align-items: center; justify-content: center; }
.employee-drawer { width: 500px; max-width: 92vw; max-height: 85vh; display: flex; flex-direction: column; border-radius: 10px; border: 1px solid var(--e-border, #E1E6EF); background: var(--e-surface, #FFFFFF); box-shadow: 0 24px 80px rgba(15,23,42,0.2); }
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
.btn-ghost { background: transparent; border: none; color: var(--c-sub); }
</style>
