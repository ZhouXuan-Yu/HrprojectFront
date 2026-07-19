<template>
  <div class="boss-integration">
    <div v-if="compact" class="boss-compact">
      <span class="boss-status" :class="statusState">BOSS 直聘 {{ statusState === 'connected' ? '已连接' : '未连接' }}</span>
    </div>
    <div v-else class="boss-full">
      <!-- Full integration panel placeholder -->
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

defineProps({
  compact: { type: Boolean, default: false },
});

const statusState = ref('disconnected');
const showBossLoginModal = ref(false);
const loginLoading = ref(false);
const loginError = ref('');
let loginTimeoutId = null;

const api = { post: async () => ({ data: {} }) };

function handleLogin() {
  if (loginTimeoutId) return;
  showBossLoginModal.value = true;
  loginLoading.value = true;
  loginError.value = '';
  loginTimeoutId = setTimeout(() => {
    loginError.value = '登录超时（120s）。请确认 boss-cli 已安装且未运行其他浏览器实例。';
    loginLoading.value = false;
    loginTimeoutId = null;
  }, 120_000);
  api.post('/boss/login')
    .then((res) => {
      const data = res?.data || res || {};
      if (data?.logged_in === true || data?.success === true || data?.status === 'connected') {
        statusState.value = 'connected';
        showBossLoginModal.value = false;
      } else {
        loginError.value = data?.message || data?.error || '登录未成功，请手动扫码后在 Boss 浏览器中完成登录';
      }
    })
    .catch((e) => {
      loginError.value = e?.message || e?.error || '登录请求失败，请检查后端 /api/boss/login 端点';
    })
    .finally(() => {
      loginLoading.value = false;
      clearTimeout(loginTimeoutId);
      loginTimeoutId = null;
    });
}
function dismissBossLoginModal() {
  showBossLoginModal.value = false;
  loginError.value = '';
  if (loginTimeoutId) {
    clearTimeout(loginTimeoutId);
    loginTimeoutId = null;
  }
  loginLoading.value = false;
}
</script>

<style scoped>
.boss-integration { font-size: 13px; }
.boss-compact { display: flex; align-items: center; gap: 8px; }
.boss-status { padding: 2px 8px; border-radius: 4px; background: var(--c-bg-alt, #f0f2f5); }
.boss-status.connected { color: var(--c-done, #22C55E); }
.boss-status.disconnected { color: var(--c-draft, #9CA3AF); }
</style>
