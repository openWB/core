<template>
  <div
    v-if="showMessage"
    class="row q-mt-sm q-pa-sm text-white no-wrap cursor-pointer rounded-borders"
    :class="[{ 'items-center': collapsed }, messageClass]"
    @click="toggleCollapse"
  >
    <q-icon :name="iconName" size="sm" class="q-mr-xs" />
    <div :class="{ ellipsis: collapsed }">
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

const messageClass = computed(() => {
  switch (props.type) {
    case 'warning':
      return 'bg-warning';
    case 'error':
      return 'bg-negative';
    default:
      return 'bg-primary';
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
