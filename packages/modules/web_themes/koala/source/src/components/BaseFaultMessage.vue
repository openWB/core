<template>
  <BaseMessage
    :show-message="props.faultState > 0"
    :message="props.message"
    :type="messageType"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import BaseMessage from './BaseMessage.vue';

const props = defineProps<{
  faultState: number;
  message: string;
}>();

const messageType = computed<'warning' | 'error'>(() =>
  props.faultState >= 2 ? 'error' : 'warning',
);
</script>
