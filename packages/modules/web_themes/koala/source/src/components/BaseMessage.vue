<template>
  <div
    v-if="showMessage"
    class="message-bar row q-mt-sm q-pa-sm no-wrap cursor-pointer rounded-borders"
    :class="{ 'items-center': collapsed }"
    @click="toggleCollapse"
  >
    <div class="flex flex-center q-mr-sm">
      <q-icon :name="iconName" size="sm" class="message-icon" />
    </div>
    <div class="message-text self-center" :class="{ ellipsis: collapsed }">
      {{ message }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';

const props = withDefaults(
  defineProps<{
    showMessage?: boolean;
    message: string;
    type?: 'info' | 'warning' | 'error';
    collapsed?: boolean;
  }>(),
  {
    collapsed: true,
    showMessage: true,
  },
);

const collapsed = ref(props.collapsed);

const toggleCollapse = () => {
  collapsed.value = !collapsed.value;
};

const messageColor = computed(() => {
  switch (props.type) {
    case 'warning':
      return 'var(--q-warning)';
    case 'error':
      return 'var(--q-negative)';
    default:
      return 'var(--q-primary)';
  }
});

const iconName = computed(() => {
  switch (props.type) {
    case 'warning':
      return 'warning';
    case 'error':
      return 'error';
    default:
      return 'info';
  }
});
</script>

<style scoped>
.message-bar {
  background-color: color-mix(in srgb, v-bind(messageColor) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--q-text) 35%, transparent);
}

.message-text {
  color: var(--q-text);
}

.message-icon {
  color: v-bind(messageColor);
}
</style>
