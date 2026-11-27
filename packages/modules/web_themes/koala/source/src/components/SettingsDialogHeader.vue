<template>
  <div class="row no-wrap items-center justify-between settings-header-actions">
    <q-btn
      icon="close"
      flat
      round
      dense
      class="settings-header-action"
      aria-label="Schließen"
      :disable="saving"
      @click="$emit('close')"
    />
    <q-btn
      icon="check"
      color="primary"
      flat
      round
      dense
      class="settings-header-action"
      aria-label="Änderungen übernehmen"
      :loading="saving"
      @click="$emit('apply')"
    />
  </div>
  <div class="text-h6 settings-header-name q-mt-sm" :title="name">
    {{ name }}
  </div>
  <div v-if="subtitle" class="text-subtitle2">{{ subtitle }}</div>
</template>

<script setup lang="ts">
defineProps<{ name?: string; subtitle?: string; saving: boolean }>();
defineEmits<{ close: []; apply: [] }>();
</script>

<style scoped>
.settings-header-actions {
  margin-inline: -6px;
}
.settings-header-action {
  flex: 0 0 36px;
  width: 36px;
  min-width: 36px;
  max-width: 36px;
  height: 36px;
  min-height: 36px;
  max-height: 36px;
  border-radius: 50%;
}
.settings-header-action :deep(.q-icon) {
  width: 24px;
  height: 24px;
  font-size: 24px;
  line-height: 1;
}
.settings-header-name {
  overflow-wrap: anywhere;
}
</style>
