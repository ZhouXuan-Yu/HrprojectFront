<template>
  <div class="boss-login-overlay" @click.self="cancel">
    <div class="boss-login-card" role="dialog" aria-modal="true" aria-label="BOSS直聘登录">
      <div class="boss-login-header">
        <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
        <h2>BOSS 直聘 · 扫码登录</h2>
        <button class="boss-login-close" @click="cancel" aria-label="关闭">✕</button>
      </div>

      <div class="boss-login-body">
        <!-- Step 1: launch browser -->
        <div v-if="step === 'launch'" class="boss-step">
          <p class="boss-hint">点击下方按钮，系统将通过 <code>boss-cli</code> 自动打开 BOSS 直聘登录页面。</p>
          <p class="boss-sub">登录过程完全在您的本地浏览器中完成，系统不会获取您的密码。</p>
          <button class="btn btn-primary boss-wide-btn" :disabled="loading" @click="launchLogin">
            <span v-if="loading" class="spinner"></span>
            {{ loading ? '正在打开浏览器...' : '打开 BOSS 登录页' }}
          </button>
          <p v-if="loginUrl && !loading" class="boss-url">
            如果浏览器未自动打开，请手动访问：
            <a :href="loginUrl" target="_blank" rel="noopener">{{ loginUrl }}</a>
          </p>
        </div>

        <!-- Step 2: verify login -->
        <div v-if="step === 'scan'" class="boss-step">
          <div class="boss-qr-placeholder">
            <svg viewBox="0 0 24 24" width="64" height="64" stroke="var(--c-primary)" fill="none" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="3"/><circle cx="12" cy="12" r="5"/></svg>
          </div>
          <p class="boss-hint">请在打开的浏览器窗口中，使用 <strong>BOSS 直聘 App</strong> 或 <strong>微信</strong> 扫码登录。</p>
          <p class="boss-sub">登录完成后回到此页面点击下方按钮。</p>
          <div class="boss-step-actions">
            <button class="btn btn-primary boss-wide-btn" :disabled="loading" @click="verifyLogin">
              <span v-if="loading" class="spinner"></span>
              {{ loading ? '验证中...' : '验证登录状态' }}
            </button>
            <button class="btn btn-ghost boss-wide-btn" @click="step = 'launch'; loginUrl = ''">← 上一步</button>
          </div>
        </div>

        <!-- Step 3: done -->
        <div v-if="step === 'done'" class="boss-step">
          <div class="boss-done-icon">
            <svg viewBox="0 0 24 24" width="48" height="48" stroke="var(--c-done)" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          </div>
          <p class="boss-hint">✅ BOSS 直聘已连接</p>
          <p class="boss-sub">现在可以使用岗位同步、候选人搜索、打招呼和聊天功能。</p>
          <button class="btn btn-primary boss-wide-btn" @click="done">进入 BOSS 工作台</button>
        </div>

        <!-- Error -->
        <div v-if="errorMsg" class="boss-error">
          <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          {{ errorMsg }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { api } from '../api/index.js';

const emit = defineEmits(['login-success', 'cancel']);

const step = ref('launch');
const loading = ref(false);
const errorMsg = ref('');
const loginUrl = ref('');

async function launchLogin() {
  loading.value = true;
  errorMsg.value = '';
  try {
    await api.post('/boss/login');
  } catch (_) {
    // boss-cli login opens browser and returns immediately; timeout is expected
  }
  loginUrl.value = 'https://www.zhipin.com/web/user/?ka=header-login';
  step.value = 'scan';
  loading.value = false;
}

async function verifyLogin() {
  loading.value = true;
  errorMsg.value = '';
  try {
    const resp = await api.get('/boss/status');
    const data = resp?.data || resp || {};
    if (data?.logged_in === true || data?.status === 'connected' || data?.available === true) {
      step.value = 'done';
    } else {
      errorMsg.value = '尚未检测到登录状态，请在浏览器中完成扫码登录后重试。';
    }
  } catch (e) {
    errorMsg.value = '验证失败: ' + (e?.message || '网络错误');
  } finally {
    loading.value = false;
  }
}

function done() { emit('login-success'); }
function cancel() { emit('cancel'); }
</script>

<style scoped>
.boss-login-overlay {
  position: fixed; inset: 0; z-index: 400;
  background: rgba(15,23,42,0.45); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
}
.boss-login-card {
  width: 480px; max-width: 94vw; max-height: 90vh; overflow-y: auto;
  border-radius: 12px; border: 1px solid var(--c-border,#E1E6EF);
  background: var(--c-card,#FFFFFF); box-shadow: 0 24px 80px rgba(15,23,42,0.18);
}
.boss-login-header {
  display: flex; align-items: center; gap: 10px;
  padding: 18px 24px; border-bottom: 1px solid var(--c-border-soft,#EFF3F8);
}
.boss-login-header svg { color: var(--c-primary); flex-shrink: 0; }
.boss-login-header h2 { margin: 0; font-size: 16px; font-weight: 700; color: var(--c-text,#172033); flex: 1; }
.boss-login-close {
  width: 32px; height: 32px; border-radius: 50%; border: none;
  background: var(--c-surface-soft,#F2F5FA); color: var(--c-muted,#5B6475);
  cursor: pointer; font-size: 16px; display: flex; align-items: center; justify-content: center;
}
.boss-login-close:hover { background: var(--c-border,#E1E6EF); }
.boss-login-body { padding: 24px; }
.boss-step { display: flex; flex-direction: column; align-items: center; gap: 16px; text-align: center; }
.boss-hint { margin: 0; font-size: 14px; line-height: 1.7; color: var(--c-text,#172033); }
.boss-sub { margin: -8px 0 0; font-size: 12px; color: var(--c-sub,#8C95A6); }
.boss-qr-placeholder {
  width: 120px; height: 120px; border: 2px dashed var(--c-border,#E1E6EF);
  border-radius: 12px; display: flex; align-items: center; justify-content: center; margin: 8px 0;
}
.boss-done-icon { margin: 8px 0; }
.boss-wide-btn { width: 100%; justify-content: center; padding: 10px 20px; }
.boss-step-actions { width: 100%; display: flex; flex-direction: column; gap: 8px; }
.boss-error {
  display: flex; align-items: center; gap: 8px; margin-top: 16px;
  padding: 10px 14px; background: #FEF2F2; border: 1px solid #FECACA;
  border-radius: 8px; font-size: 13px; color: #EF4444;
}
.boss-url { font-size: 12px; color: var(--c-muted,#5B6475); word-break: break-all; margin: 0; }
.boss-url a { color: var(--c-primary,#4F6EF7); }

.btn { display: inline-flex; align-items: center; gap: 6px; border-radius: 8px; font-size: 14px; font-weight: 700; cursor: pointer; border: none; transition: all 0.15s; font-family: inherit; }
.btn:active { transform: scale(0.98); }
.btn:disabled { opacity: 0.5; pointer-events: none; }
.btn-primary { background: var(--c-primary,#4F6EF7); color: #fff; }
.btn-primary:hover:not(:disabled) { background: #3D54D4; }
.btn-ghost { background: var(--c-surface-soft,#F2F5FA); border: 1px solid var(--c-border,#E1E6EF); color: var(--c-muted,#5B6475); }
.btn-ghost:hover { background: var(--c-border-soft,#EFF3F8); color: var(--c-text,#172033); }

.spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff; border-radius: 50%; animation: spin 0.6s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
