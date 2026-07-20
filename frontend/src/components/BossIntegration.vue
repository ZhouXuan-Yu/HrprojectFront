<template>
  <div class="boss-integration">
    <div v-if="compact" class="boss-compact">
      <span class="boss-status" :class="statusState">
        <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor" style="vertical-align:-1px;margin-right:4px">
          <circle cx="12" cy="12" r="10"/>
        </svg>
        BOSS 直聘 {{ statusLabel }}
      </span>
      <button v-if="statusState === 'disconnected' || statusState === 'unavailable'" class="btn btn-outline btn-sm" @click="handleLogin" :disabled="loginLoading">
        {{ loginLoading ? '连接中...' : '连接' }}
      </button>
      <button v-if="statusState === 'connecting'" class="btn btn-ghost btn-sm" @click="checkLoginStatus" :disabled="loginChecking">
        {{ loginChecking ? '验证中...' : '验证登录' }}
      </button>
      <button v-if="statusState === 'connected'" class="btn btn-ghost btn-sm" @click="statusState = 'disconnected'">断开</button>
    </div>

    <!-- Login modal -->
    <Teleport to="body">
      <div v-if="showBossLoginModal" class="boss-modal-overlay" @click.self="dismissBossLoginModal">
        <div class="boss-modal-box" role="dialog" aria-modal="true" aria-label="BOSS直聘登录">
          <div class="boss-modal-header">
            <h3>BOSS直聘连接</h3>
            <button class="boss-modal-close" @click="dismissBossLoginModal" aria-label="关闭">&#10005;</button>
          </div>
          <div class="boss-modal-body">
            <div v-if="loginLoading" class="boss-loading-state">
              <div class="boss-spinner"></div>
              <p>正在连接 BOSS 直聘...</p>
              <p class="boss-hint">系统正在打开 BOSS 登录页面</p>
            </div>
            <div v-else-if="loginResult === 'launched'" class="boss-launched-state">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--c-primary)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
              <p>已打开 BOSS 登录页面</p>
              <p class="boss-hint">请在浏览器窗口中扫码登录（使用 BOSS 直聘 App 或微信扫码）</p>
              <p class="boss-hint">登录状态会<strong>持久化保存</strong>，重启后无需重新登录</p>
              <div class="boss-step-actions">
                <button class="btn btn-primary boss-wide-btn" :disabled="loginChecking" @click="checkLoginStatus">
                  <span v-if="loginChecking" class="boss-spinner" style="width:14px;height:14px;margin:0 4px 0 0;display:inline-block"></span>
                  {{ loginChecking ? '验证中...' : '验证登录状态' }}
                </button>
              </div>
            </div>
            <div v-else-if="loginError" class="boss-error-state">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="1.5" stroke-linecap="round">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              <p class="boss-error-msg">{{ loginError }}</p>
              <button class="btn btn-primary btn-sm" @click="handleLogin">重试</button>
              <button class="btn btn-ghost btn-sm" @click="dismissBossLoginModal">取消</button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { api } from '../api/index.js'
import { useToast } from '../composables/useToast.js'

const props = defineProps({ compact: { type: Boolean, default: false } })
const { toast } = useToast()

const statusState = ref('disconnected')
const showBossLoginModal = ref(false)
const loginLoading = ref(false)
const loginError = ref('')
const loginResult = ref('')
const loginChecking = ref(false)

const statusLabel = computed(() => ({
  disconnected: '未连接',
  connecting: '等待登录...',
  connected: '已连接',
  unavailable: '不可用',
}[statusState.value] || statusState.value))

async function handleLogin() {
  showBossLoginModal.value = true
  loginLoading.value = true
  loginError.value = ''
  loginResult.value = ''
  try {
    const res = await api.post('/boss/login')
    const data = res?.data || res || {}
    if (data?.login_url) {
      loginResult.value = 'launched'
      statusState.value = 'connecting'
      toast.success('BOSS 登录页面已打开，请扫码')
    } else {
      loginError.value = data?.message || '无法启动登录页面'
    }
  } catch (e) {
    loginError.value = e?.message || '登录请求失败 — boss-cli 可能未安装。请执行: npm i -g @joohw/boss-cli'
  } finally {
    loginLoading.value = false
  }
}

async function checkLoginStatus() {
  loginChecking.value = true
  try {
    const res = await api.get('/boss/status')
    const data = res?.data || res || {}
    if (data?.logged_in || data?.status === 'connected') {
      statusState.value = 'connected'
      showBossLoginModal.value = false
      toast.success('BOSS 直聘已连接（登录状态持久化，无需重复登录）')
    } else if (data?.available) {
      loginError.value = '尚未检测到登录。请确认已在浏览器中完成扫码登录后重试。'
    } else {
      loginError.value = 'boss-cli 未安装或未启用。请执行: npm i -g @joohw/boss-cli'
    }
  } catch (e) {
    loginError.value = '验证请求失败: ' + (e?.message || '网络错误')
  } finally {
    loginChecking.value = false
  }
}

function dismissBossLoginModal() {
  showBossLoginModal.value = false
  loginError.value = ''
  loginResult.value = ''
  loginLoading.value = false
  loginChecking.value = false
}
</script>

<style scoped>
.boss-integration { font-size: 13px; }
.boss-compact { display: flex; align-items: center; gap: 8px; }
.boss-status { display: inline-flex; align-items: center; padding: 2px 10px; border-radius: 4px; background: var(--c-bg-alt, #f0f2f5); font-size: 12px; }
.boss-status.disconnected { color: var(--c-draft, #9CA3AF); }
.boss-status.connecting { color: var(--c-warn, #F59E0B); }
.boss-status.connected { color: var(--c-done, #22C55E); }
.boss-status.unavailable { color: var(--c-reject, #EF4444); }

.boss-modal-overlay {
  position: fixed; inset: 0;
  background: rgba(15,23,42,0.38);
  backdrop-filter: blur(2px);
  z-index: 500;
  display: flex; align-items: center; justify-content: center;
}
.boss-modal-box {
  width: 420px; max-width: 94vw;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 24px 80px rgba(15,23,42,0.2);
}
.boss-modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; border-bottom: 1px solid #EFF3F8;
}
.boss-modal-header h3 { margin: 0; font-size: 16px; font-weight: 700; color: #172033; }
.boss-modal-close {
  width: 28px; height: 28px; border-radius: 6px;
  border: none; background: transparent;
  color: #8C95A6; cursor: pointer; font-size: 14px;
}
.boss-modal-close:hover { background: #F2F5FA; color: #172033; }
.boss-modal-body { padding: 28px 20px; text-align: center; }
.boss-loading-state p, .boss-launched-state p { margin: 8px 0 0; font-size: 14px; color: #172033; }
.boss-hint { font-size: 12px !important; color: #8C95A6 !important; margin-top: 4px !important; }
.boss-spinner {
  width: 32px; height: 32px; border: 3px solid #E1E6EF;
  border-top-color: #4F6EF7; border-radius: 50%;
  margin: 0 auto 12px; animation: boss-spin 0.8s linear infinite;
}
@keyframes boss-spin { to { transform: rotate(360deg); } }
.boss-error-state p { margin: 12px 0; font-size: 13px; color: #EF4444; line-height: 1.6; }
.boss-error-msg { word-break: break-word; }
.boss-launched-state svg { margin-bottom: 4px; }
.boss-step-actions { margin-top: 16px; display: flex; flex-direction: column; gap: 8px; align-items: center; }
.boss-wide-btn { width: 100%; max-width: 260px; justify-content: center; padding: 10px 18px; }
</style>
