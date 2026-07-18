import { ref, computed } from 'vue';

export function useAiTab() {
  const loading = ref(false);
  const error = ref('');
  const status = computed(() => loading.value ? 'submitted' : (error.value ? 'error' : 'ready'));

  function resetError() { error.value = ''; }

  return { loading, error, status, resetError };
}
