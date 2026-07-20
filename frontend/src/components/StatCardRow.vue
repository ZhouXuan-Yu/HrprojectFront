<template>
  <!-- 统一统计卡行（人才库 hero-summary-card 同款），可直接用于各业务页导航栏下方 -->
  <div class="stat-card-row" :style="rowStyle">
    <article
      v-for="c in cards"
      :key="c.key || c.label"
      class="hero-summary-card stat-card"
      :class="{ 'is-active': activeKey === c.key, 'is-clickable': clickable }"
      :role="clickable ? 'button' : undefined"
      :tabindex="clickable ? 0 : undefined"
      :aria-label="clickable ? c.label + '，' + c.value + '，点击筛选' : undefined"
      @click="onSelect(c)"
      @keydown.enter.space.prevent="onSelect(c)"
    >
      <span>{{ c.label }}</span>
      <strong>{{ c.value }}</strong>
      <em>{{ c.hint }}</em>
      <i class="stat-card-icon" v-html="c.icon"></i>
    </article>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  // [{ key, label, value, hint, icon }]  icon 为 kpiIcons.js 的 svg 字符串
  cards: { type: Array, required: true },
  activeKey: { type: String, default: '' },
  clickable: { type: Boolean, default: false },
  cols: { type: Number, default: 0 }, // 0 = 按卡片数自动
});
const emit = defineEmits(['select']);

const colCount = computed(() => props.cols || props.cards.length || 4);
const rowStyle = computed(() => ({ gridTemplateColumns: `repeat(${colCount.value}, minmax(0, 1fr))` }));

function onSelect(c) {
  if (props.clickable) emit('select', c);
}
</script>

<style scoped>
.stat-card-row { display: grid; gap: 12px; margin-bottom: 16px; }
.stat-card { transition: border-color .15s, box-shadow .15s; }
.stat-card.is-clickable { cursor: pointer; }
.stat-card.is-clickable:hover { border-color: var(--c-primary); }
.stat-card.is-active {
  border-color: var(--c-primary);
  box-shadow: 0 0 0 3px var(--c-primary-subtle);
}
/* 图标块内放蓝色线性图标（隐藏 hero-summary-card 默认彩色圆点装饰） */
.stat-card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-primary);
}
.stat-card-icon::after { display: none; }
.stat-card-icon svg { width: 18px; height: 18px; }

@media (max-width: 1200px) { .stat-card-row { grid-template-columns: repeat(3, minmax(0, 1fr)) !important; } }
@media (max-width: 720px) { .stat-card-row { grid-template-columns: repeat(2, minmax(0, 1fr)) !important; } }
</style>
