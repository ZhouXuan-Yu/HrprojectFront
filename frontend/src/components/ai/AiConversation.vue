<template>
  <div
    ref="scrollEl"
    data-slot="ai-conversation"
    role="log"
    aria-live="polite"
    @scroll.passive="onScroll"
  >
    <slot />
    <!-- 回到底部按钮：内容溢出且用户不在底部时浮现 -->
    <button
      data-slot="ai-conversation-scroll-bottom"
      type="button"
      :data-state="showScrollButton ? 'visible' : 'hidden'"
      :aria-hidden="showScrollButton ? 'false' : 'true'"
      :tabindex="showScrollButton ? 0 : -1"
      aria-label="回到底部"
      @click="scrollToBottom(true)"
    >
      <svg viewBox="0 0 24 24" style="width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:round" aria-hidden="true">
        <polyline points="6 9 12 15 18 9"/>
      </svg>
    </button>
  </div>
</template>

<script setup>
/**
 * AiConversation — AI 对话滚动容器（设计转译自 HeroUIPro chat-conversation）
 *
 * 核心交互：
 * - role="log" + aria-live，语义化对话日志
 * - ResizeObserver / MutationObserver 监测内容变化
 * - 用户停留在底部时，新内容自动跟随滚动到底
 * - 有溢出且不在底部时浮现「回到底部」圆形按钮（data-state visible/hidden）
 */
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue';

const scrollEl = ref(null);
const showScrollButton = ref(false);
const isUserNearBottom = ref(true);

let resizeObserver = null;
let mutationObserver = null;

function isNearBottom() {
  const el = scrollEl.value;
  if (!el) return true;
  return el.scrollHeight - el.scrollTop - el.clientHeight < 60;
}

function onScroll() {
  const near = isNearBottom();
  isUserNearBottom.value = near;
  showScrollButton.value = !near;
}

function scrollToBottom(smooth = false) {
  const el = scrollEl.value;
  if (!el) return;
  nextTick(() => {
    if (!scrollEl.value) return;
    scrollEl.value.scrollTo({
      top: scrollEl.value.scrollHeight,
      behavior: smooth ? 'smooth' : 'auto',
    });
  });
}

function onContentChange() {
  if (isUserNearBottom.value) {
    scrollToBottom(false);
  }
}

onMounted(() => {
  const el = scrollEl.value;
  if (!el) return;

  if (typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(onContentChange);
    resizeObserver.observe(el);
    // 同时观察第一个子节点（内容高度变化）
    if (el.firstElementChild) resizeObserver.observe(el.firstElementChild);
  }
  if (typeof MutationObserver !== 'undefined') {
    mutationObserver = new MutationObserver(onContentChange);
    mutationObserver.observe(el, { childList: true, subtree: true, characterData: true });
  }
  nextTick(() => scrollToBottom(false));
});

onBeforeUnmount(() => {
  if (resizeObserver) { resizeObserver.disconnect(); resizeObserver = null; }
  if (mutationObserver) { mutationObserver.disconnect(); mutationObserver = null; }
});
</script>

<style scoped>
[data-slot="ai-conversation"] {
  position: relative;
  min-height: 0;
  scrollbar-width: thin;
  scrollbar-color: var(--c-border-light, #EFF1F5) transparent;
}

/* 回到底部按钮：sticky 吸附在滚动视口底部右侧 */
[data-slot="ai-conversation-scroll-bottom"] {
  position: sticky;
  bottom: 12px;
  margin-left: auto;
  margin-right: 8px;
  margin-top: -40px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid var(--c-border, #E1E6EF);
  background: var(--c-card, #FFFFFF);
  color: var(--c-sub, #8C95A6);
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(23, 32, 51, 0.08);
  transition: opacity 0.2s ease, transform 0.2s ease, background 0.15s, color 0.15s;
  z-index: 10;
}
[data-slot="ai-conversation-scroll-bottom"][data-state="hidden"] {
  opacity: 0;
  transform: translateY(8px);
  pointer-events: none;
}
[data-slot="ai-conversation-scroll-bottom"][data-state="visible"] {
  opacity: 1;
  transform: translateY(0);
}
[data-slot="ai-conversation-scroll-bottom"]:hover {
  background: var(--c-primary-subtle, rgba(79, 110, 247, 0.08));
  color: var(--c-primary, #4F6EF7);
}
[data-slot="ai-conversation-scroll-bottom"]:focus-visible {
  outline: 2px solid var(--c-primary, #4F6EF7);
  outline-offset: 2px;
}

@media (prefers-reduced-motion: reduce) {
  [data-slot="ai-conversation-scroll-bottom"] {
    transition: none;
  }
  [data-slot="ai-conversation-scroll-bottom"][data-state="hidden"] {
    transform: none;
  }
}

@media (max-width: 768px) {
  [data-slot="ai-conversation-scroll-bottom"] {
    width: 30px;
    height: 30px;
    bottom: 8px;
    margin-right: 4px;
  }
}
</style>
