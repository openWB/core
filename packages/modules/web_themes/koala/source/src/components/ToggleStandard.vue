<template>
  <q-toggle
    :model-value="props.value"
    @update:model-value="emitValue"
    :color="props.value ? 'positive' : 'negative'"
    :size="props.size"
  />
</template>

<script setup lang="ts">
const props = defineProps({
  value: {
    type: Boolean,
    default: false,
  },
  size: {
    type: String,
    default: 'lg',
  },
});

const emit = defineEmits<{
  'update:value': [value: boolean];
}>();

const emitValue = (newValue: boolean) => {
  emit('update:value', newValue);
};
</script>
