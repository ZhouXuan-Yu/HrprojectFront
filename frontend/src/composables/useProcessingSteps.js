// useProcessingSteps — 阻塞式 AI 工作流的「分步处理过程」进度
// 注意：这不是真实的 AI 思考链，UI 文案必须诚实标注为「处理过程」。
import { ref, onBeforeUnmount } from 'vue';

/**
 * @param {string[]} labels - 各步骤文案
 * @param {number} stepMs - 每步推进间隔（毫秒）
 */
export function useProcessingSteps(labels, stepMs = 650) {
  const steps = ref(labels.map((label) => ({ label, status: 'pending' })));
  const active = ref(false);
  const hasRun = ref(false);

  let timer = null;
  let idx = 0;

  function _stopTimer() {
    if (timer) { clearInterval(timer); timer = null; }
  }

  function start() {
    _stopTimer();
    idx = 0;
    steps.value = labels.map((label, i) => ({ label, status: i === 0 ? 'running' : 'pending' }));
    active.value = true;
    hasRun.value = true;
    timer = setInterval(() => {
      if (idx < steps.value.length - 1) {
        steps.value[idx].status = 'done';
        idx += 1;
        steps.value[idx].status = 'running';
      }
    }, stepMs);
  }

  function finish() {
    _stopTimer();
    steps.value = steps.value.map((s) => ({ ...s, status: 'done' }));
    active.value = false;
  }

  function reset() {
    _stopTimer();
    active.value = false;
    hasRun.value = false;
    steps.value = labels.map((label) => ({ label, status: 'pending' }));
  }

  onBeforeUnmount(_stopTimer);

  return { steps, active, hasRun, start, finish, reset };
}
