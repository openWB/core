<template>
  <q-toggle
    :model-value="props.value"
    @update:model-value="emitValue"
    :color="props.value ? 'positive' : 'negative'"
    size="lg"
  />
</template>

<script setup lang="ts">
const props = defineProps({
  value: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits<{
  'update:value': [value: boolean];
}>();

const emitValue = (newValue: boolean) => {
  emit('update:value', newValue);
};
</script>
