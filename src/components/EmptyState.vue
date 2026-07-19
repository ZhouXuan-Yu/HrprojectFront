<template>
  <div class="empty-state">
    <div class="empty-state-illustration" aria-hidden="true">
      <svg width="120" height="100" viewBox="0 0 120 100" fill="none" xmlns="http://www.w3.org/2000/svg">
        <!-- Table outline -->
        <rect x="10" y="40" width="100" height="45" rx="6" stroke="#E1E6EF" stroke-width="1.5" fill="#F9FAFC"/>
        <!-- Table header row -->
        <rect x="16" y="45" width="88" height="10" rx="3" fill="#EFF1F5"/>
        <rect x="16" y="58" width="88" height="8" rx="3" fill="#F0F2F5" opacity="0.6"/>
        <rect x="16" y="68" width="88" height="8" rx="3" fill="#F0F2F5" opacity="0.6"/>
        <rect x="16" y="78" width="88" height="8" rx="3" fill="#F0F2F5" opacity="0.6"/>
        <!-- Search icon -->
        <circle cx="60" cy="24" r="14" stroke="#D1D5DB" stroke-width="1.5" fill="#F9FAFC"/>
        <circle cx="55" cy="20" r="4" fill="#E1E6EF"/>
        <line x1="65" y1="28" x2="72" y2="35" stroke="#D1D5DB" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
    </div>
    <h3 class="empty-state-title">{{ title }}</h3>
    <p v-if="description" class="empty-state-description">{{ description }}</p>
    <a
      v-if="actionLabel && actionLink"
      :href="actionLink"
      class="empty-state-action btn btn-primary btn-sm"
    >{{ actionLabel }}</a>
    <button
      v-else-if="actionLabel && !actionLink"
      class="empty-state-action btn btn-primary btn-sm"
      @click="$emit('action')"
    >{{ actionLabel }}</button>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, default: '暂无数据' },
  description: { type: String, default: '' },
  actionLabel: { type: String, default: '' },
  actionLink: { type: String, default: '' },
})

defineEmits(['action'])
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
  min-height: 240px;
}

.empty-state-illustration {
  margin-bottom: 16px;
  opacity: 0.7;
}

.empty-state-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--c-text, #172033);
  margin: 0 0 8px;
}

.empty-state-description {
  font-size: 13px;
  color: var(--c-sub, #5B6475);
  margin: 0 0 20px;
  line-height: 1.6;
  max-width: 320px;
}

.empty-state-action {
  text-decoration: none;
}
</style>
