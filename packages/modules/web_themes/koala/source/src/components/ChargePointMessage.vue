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
import { useMqttStore } from 'src/stores/mqtt-store';
import { computed, ref } from 'vue';

const props = defineProps<{
  chargePointId: number
  faultMessage?: boolean
}>();

const mqttStore = useMqttStore();
const collapsed = ref<boolean>(true);

const toggleCollapse = () => {
  collapsed.value = !collapsed.value;
};

const showMessage = computed(() => {
  return state.value !== undefined && state.value !== 0;
});

const state = computed(() =>
  props.faultMessage
    ? mqttStore.chargePointFaultState(props.chargePointId)
    : -1
);

const message = computed(() =>
  props.faultMessage
    ? mqttStore.chargePointFaultMessage(props.chargePointId)
    : mqttStore.chargePointStateMessage(props.chargePointId),
);

const messageClass = computed(() => {
  switch (state.value) {
    case 1:
      return 'bg-warning';
    case 2:
      return 'bg-negative';
    default:
      return 'bg-primary';
  }
});

const iconName = computed(() => {
  switch (state.value) {
    case 1:
      return 'warning';
    case 2:
      return 'error';
    default:
      return 'info';
  }
});
</script>
