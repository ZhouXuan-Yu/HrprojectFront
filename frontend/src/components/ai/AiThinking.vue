<template>
  <div
    data-slot="ai-thinking"
    :data-expanded="expanded ? 'true' : 'false'"
    :data-active="active ? 'true' : 'false'"
    :data-mode="mode"
  >
    <!-- Header: icon + title + chevron -->
    <button
      data-slot="ai-thinking-header"
      type="button"
      :aria-expanded="expanded ? 'true' : 'false'"
      :aria-label="expanded ? '收起' + title : '展开' + title"
      @click="toggle"
    >
      <span data-slot="ai-thinking-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" style="width:15px;height:15px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round">
          <path d="M9.5 2a5.5 5.5 0 0 0-3.3 9.9c.8.7 1.3 1.7 1.3 2.8V16h4v-1.3c0-1.1.5-2.1 1.3-2.8A5.5 5.5 0 0 0 9.5 2z"/>
          <line x1="8" y1="19" x2="11" y2="19"/>
          <line x1="8.5" y1="22" x2="10.5" y2="22"/>
        </svg>
      </span>
      <span data-slot="ai-thinking-title">{{ headerText }}</span>
      <span v-if="active" data-slot="ai-thinking-live-dot" aria-hidden="true"></span>
      <span data-slot="ai-thinking-chevron" aria-hidden="true">
        <svg viewBox="0 0 24 24" style="width:13px;height:13px;stroke:currentColor;fill:none;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:round">
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </span>
    </button>

    <!-- Body -->
    <div v-show="expanded" data-slot="ai-thinking-body">
      <!-- Text mode: streaming thinking content -->
      <div v-if="mode === 'text'" data-slot="ai-thinking-text" ref="textBody">
        <span>{{ thinking || (active ? '正在整理思路…' : '暂无思考记录') }}</span><span v-if="active" data-slot="ai-thinking-caret" aria-hidden="true"></span>
      </div>

      <!-- Steps mode: honest step-by-step processing progress -->
      <ol v-else data-slot="ai-thinking-steps">
        <li
          v-for="(step, i) in steps"
          :key="i"
          data-slot="ai-thinking-step"
          :data-status="step.status"
        >
          <span data-slot="ai-thinking-step-indicator" aria-hidden="true">
            <svg v-if="step.status === 'done'" viewBox="0 0 24 24" style="width:13px;height:13px;stroke:var(--c-done, #22C55E);fill:none;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:round">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            <span v-else-if="step.status === 'running'" data-slot="ai-thinking-step-dot-running"></span>
            <span v-else data-slot="ai-thinking-step-dot-pending"></span>
          </span>
          <span data-slot="ai-thinking-step-label" :data-status="step.status">{{ step.label }}</span>
        </li>
      </ol>
    </div>
  </div>
</template>

<script setup>
/**
 * AiThinking — 可折叠「思考过程 / 处理过程」面板
 *
 * 两种模式：
 * - text（默认）：流式期间实时显示 thinking 文本，带打字光标效果
 * - steps（传入 steps 数组）：分步处理进度，逐步点亮。
 *   用于无真实 thinking 数据的阻塞式工作流，文案必须诚实标注为「处理过程」。
 *
 * 交互：active 时自动展开；结束后自动收起为摘要（doneText）。
 * 无渐变、无 emoji，遵循 --c-* token，支持 prefers-reduced-motion。
 */
import { ref, computed, watch, onBeforeUnmount } from 'vue';

const props = defineProps({
  thinking: { type: String, default: '' },
  steps: { type: Array, default: () => [] },
  active: { type: Boolean, default: false },
  title: { type: String, default: '思考过程' },
  doneText: { type: String, default: '思考完成 · 点击展开' },
});

const mode = computed(() => (props.steps && props.steps.length ? 'steps' : 'text'));

const expanded = ref(true);
const hasRun = ref(props.active);
const textBody = ref(null);
let collapseTimer = null;

// 流式期间思考文本持续增长时，面板内部自动跟随滚动到底部
watch(
  () => props.thinking,
  () => {
    if (!props.active) return;
    const el = textBody.value;
    if (el) el.scrollTop = el.scrollHeight;
  }
);

const headerText = computed(() => {
  if (!props.active && hasRun.value && !expanded.value) return props.doneText;
  return props.title;
});

function toggle() {
  expanded.value = !expanded.value;
}

watch(
  () => props.active,
  (val) => {
    if (val) {
      hasRun.value = true;
      expanded.value = true;
      if (collapseTimer) { clearTimeout(collapseTimer); collapseTimer = null; }
    } else if (hasRun.value) {
      // 结束后延迟收起为摘要
      collapseTimer = setTimeout(() => { expanded.value = false; }, 800);
    }
  }
);

onBeforeUnmount(() => {
  if (collapseTimer) clearTimeout(collapseTimer);
});
</script>

<style scoped>
[data-slot="ai-thinking"] {
  margin: 4px 0 8px 42px;
  border: 1px solid var(--c-border, #E1E6EF);
  border-radius: var(--radius, 8px);
  background: var(--c-card, #FFFFFF);
  overflow: hidden;
}

/* Header */
[data-slot="ai-thinking-header"] {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 12px;
  background: none;
  border: none;
  font-family: inherit;
  font-size: var(--fs-caption, 12px);
  color: var(--c-sub, #8C95A6);
  cursor: pointer;
  user-select: none;
  text-align: left;
  transition: background 0.15s;
}
[data-slot="ai-thinking-header"]:hover {
  background: var(--c-surface-elevated, #F9FAFC);
}
[data-slot="ai-thinking-header"]:focus-visible {
  outline: 2px solid var(--c-primary, #4F6EF7);
  outline-offset: -2px;
}

[data-slot="ai-thinking-icon"] {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  color: var(--c-primary, #4F6EF7);
}

[data-slot="ai-thinking-title"] {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
[data-slot="ai-thinking"][data-active="true"] [data-slot="ai-thinking-title"] {
  color: var(--c-body, #5B6475);
}

/* Live dot while active */
[data-slot="ai-thinking-live-dot"] {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--c-primary, #4F6EF7);
  flex-shrink: 0;
  animation: ai-thinking-pulse 1.2s ease-in-out infinite;
}
@keyframes ai-thinking-pulse {
  0%, 100% { opacity: 0.35; }
  50% { opacity: 1; }
}

/* Chevron */
[data-slot="ai-thinking-chevron"] {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  transition: transform 0.2s ease;
}
[data-slot="ai-thinking"][data-expanded="true"] [data-slot="ai-thinking-chevron"] {
  transform: rotate(180deg);
}

/* Body */
[data-slot="ai-thinking-body"] {
  padding: 2px 12px 12px;
  border-top: 1px solid var(--c-border-light, #EFF1F5);
}

/* Text mode */
[data-slot="ai-thinking-text"] {
  padding-top: 10px;
  font-size: var(--fs-caption, 12px);
  line-height: 1.7;
  color: var(--c-body, #5B6475);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 240px;
  overflow-y: auto;
}
[data-slot="ai-thinking-caret"] {
  display: inline-block;
  width: 2px;
  height: 1em;
  margin-left: 2px;
  vertical-align: text-bottom;
  background: var(--c-primary, #4F6EF7);
  animation: ai-thinking-blink 1s step-end infinite;
}
@keyframes ai-thinking-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* Steps mode */
[data-slot="ai-thinking-steps"] {
  list-style: none;
  margin: 0;
  padding: 8px 0 0;
}
[data-slot="ai-thinking-step"] {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 4px 0;
}
[data-slot="ai-thinking-step"][data-status="pending"] {
  opacity: 0.45;
}
[data-slot="ai-thinking-step-indicator"] {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 15px;
  padding-top: 3px;
  flex-shrink: 0;
}
[data-slot="ai-thinking-step-dot-pending"] {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--c-sub, #8C95A6);
}
[data-slot="ai-thinking-step-dot-running"] {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--c-primary, #4F6EF7);
  animation: ai-thinking-pulse 1.2s ease-in-out infinite;
}
[data-slot="ai-thinking-step-label"] {
  font-size: var(--fs-caption, 12px);
  line-height: 1.6;
  color: var(--c-body, #5B6475);
}
[data-slot="ai-thinking-step-label"][data-status="running"] {
  color: var(--c-text, #172033);
  font-weight: 600;
}
[data-slot="ai-thinking-step-label"][data-status="done"] {
  color: var(--c-sub, #8C95A6);
}

@media (prefers-reduced-motion: reduce) {
  [data-slot="ai-thinking-live-dot"],
  [data-slot="ai-thinking-step-dot-running"] {
    animation: none;
    opacity: 1;
  }
  [data-slot="ai-thinking-caret"] {
    animation: none;
    opacity: 1;
  }
  [data-slot="ai-thinking-chevron"] {
    transition: none;
  }
}

@media (max-width: 768px) {
  [data-slot="ai-thinking"] {
    margin-left: 32px;
  }
  [data-slot="ai-thinking-header"] {
    padding: 7px 10px;
    font-size: 11px;
  }
  [data-slot="ai-thinking-body"] {
    padding: 2px 10px 10px;
  }
}
</style>
