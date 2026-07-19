<template>
  <Teleport to="body">
    <div
      class="drawer-overlay"
      :class="{ open: visible }"
      v-if="visible || isAnimating"
      @click.self="close"
    >
      <div
        class="drawer-panel"
        role="dialog"
        :aria-modal="true"
        :aria-label="title"
      >
        <div class="drawer-header">
          <h2 class="drawer-title">{{ title }}</h2>
          <button class="drawer-close-btn" @click="close" aria-label="关闭">✕</button>
        </div>
        <div class="drawer-body">
          <slot></slot>
        </div>
        <div class="drawer-actions" v-if="$slots.actions">
          <slot name="actions"></slot>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue';

const props = defineProps({
  visible: { type: Boolean, default: false },
  title: { type: String, default: '' },
});

const emit = defineEmits(['close']);
const isAnimating = ref(false);

function close() {
  emit('close');
}

function onKeydown(e) {
  if (e.key === 'Escape' && props.visible) {
    close();
  }
}

watch(() => props.visible, (v) => {
  if (v) {
    isAnimating.value = true;
  } else {
    setTimeout(() => {
      isAnimating.value = false;
    }, 300);
  }
});

onMounted(() => {
  document.addEventListener('keydown', onKeydown);
});

onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown);
});
</script>

<style scoped>
.drawer-overlay {
  position: fixed;
  inset: 0;
  z-index: 500;
  display: flex;
  justify-content: flex-end;
  background: rgba(15, 23, 42, 0.38);
  backdrop-filter: blur(2px);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.drawer-overlay.open {
  opacity: 1;
}

.drawer-panel {
  width: 480px;
  height: 100vh;
  height: 100dvh;
  display: flex;
  flex-direction: column;
  background: var(--e-surface, #FFFFFF);
  border-left: 1px solid var(--e-border, #E1E6EF);
  box-shadow: -8px 0 32px rgba(0, 0, 0, 0.1);
  transform: translateX(100%);
  transition: transform 0.3s ease;
  outline: none;
}

.drawer-overlay.open .drawer-panel {
  transform: translateX(0);
}

.drawer-panel:focus-visible {
  box-shadow:
    -8px 0 32px rgba(0, 0, 0, 0.1),
    0 0 0 2px var(--e-primary, #4F6EF7);
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 64px;
  padding: 0 24px;
  border-bottom: 1px solid var(--e-border-soft, #EFF3F8);
  flex-shrink: 0;
}

.drawer-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--e-text, #172033);
  margin: 0;
}

.drawer-close-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: var(--e-surface-soft, #F2F5FA);
  border-radius: 8px;
  cursor: pointer;
  color: var(--e-muted, #5B6475);
  font-size: 14px;
  transition: background 0.15s, color 0.15s;
}

.drawer-close-btn:hover {
  background: var(--e-border-soft, #EFF3F8);
  color: var(--e-text, #172033);
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.drawer-actions {
  position: sticky;
  bottom: 0;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  padding: 12px 24px;
  border-top: 1px solid var(--e-border-soft, #EFF3F8);
  background: var(--e-surface, #FFFFFF);
  flex-shrink: 0;
}

@media (max-width: 767px) {
  .drawer-panel {
    width: 100vw;
  }
}

@media (prefers-reduced-motion: reduce) {
  .drawer-overlay,
  .drawer-panel {
    transition: none;
  }
}
</style>
