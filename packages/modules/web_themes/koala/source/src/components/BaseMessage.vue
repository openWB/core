<template>
  <div
    v-if="showMessage"
    class="row q-mt-sm q-pa-sm text-white no-wrap cursor-pointer"
    :class="[{ 'items-center': collapsed }, messageClass]"
    style="border-radius: 10px"
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

const props = defineProps<{
  showMessage: boolean;
  message: string;
  type?: 'info' | 'warning' | 'error';
}>();

const collapsed = ref(true);

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
