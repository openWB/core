<template>
  <q-dialog :model-value="modelValue" persistent>
    <q-card class="settings-discard-dialog">
      <q-card-section class="text-h6">Änderungen verwerfen?</q-card-section>
      <q-card-actions vertical class="q-pa-md q-gutter-y-sm">
        <q-btn
          label="Änderungen verwerfen"
          outline
          no-caps
          :disable="saving"
          @click="$emit('discard')"
        />
        <q-btn
          label="Änderungen übernehmen"
          color="primary"
          unelevated
          no-caps
          :loading="saving"
          @click="$emit('apply')"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
defineProps<{ modelValue: boolean; saving: boolean }>();
defineEmits<{ discard: []; apply: [] }>();
</script>

<style scoped>
.settings-discard-dialog {
  width: 400px;
  max-width: calc(100vw - 32px);
}
</style>
