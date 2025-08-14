<template>
  <div class="row items-center">
    <div class="text-subtitle2 q-mr-sm">Status:</div>
    <q-chip
      v-if="vehicleState.length < 1"
      label="Nicht zugeordnet"
      color="primary"
      class="q-ml-auto"
    >
    </q-chip>
    <q-chip
      v-for="(chargePoint, index) in vehicleState"
      :key="index"
      :icon="chargePoint.plugged ? 'power' : 'power_off'"
      :class="[{'q-ml-auto': index === 0, 'q-ml-none': index !== 0}, 'ellipsis']"
      :color="
        chargePoint.plugged
          ? chargePoint.charging
            ? 'positive'
            : 'warning'
          : 'negative'
      "
      :label="chargePoint.name"
    >
      <q-tooltip>
        {{
          chargePoint.plugged
            ? chargePoint.charging
              ? 'Lädt'
              : 'Angesteckt, lädt nicht'
            : 'Nicht angesteckt'
        }}
      </q-tooltip>
    </q-chip>
  </div>
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import { computed } from 'vue';

const props = defineProps<{
  vehicleId: number;
}>();

const mqttStore = useMqttStore();

const vehicleState = computed(() => {
  return mqttStore.vehicleConnectionState(props.vehicleId);
});
</script>
