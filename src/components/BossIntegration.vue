function handleLogin() {
  // Cancel any pending timeout before retrying
  if (loginTimeoutId) return;

  showBossLoginModal.value = true;
  loginLoading.value = true;
  loginError.value = '';

  // Set a 120s timeout before the backend call itself; the browser
  // automation may take a while to open the Boss login page.
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