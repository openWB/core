<template>
  <div v-if="props.readonly" class="q-mx-sm">
    <q-icon name="directions_car" />
    {{ connectedVehicle?.name }}
  </div>
  <q-btn-dropdown v-else color="grey" dense no-caps>
    <template #label>
      <span class="ellipsis q-ml-xs" :title="connectedVehicle?.name">
        <q-icon name="directions_car" />
        {{ connectedVehicle?.name }}
      </span>
    </template>
    <q-list>
      <q-item
        v-for="vehicle in vehicles"
        :key="vehicle.id"
        clickable
        v-close-popup
        dense
        @click="connectedVehicle = vehicle"
      >
        <q-item-section>
          <q-item-label class="ellipsis" :title="vehicle.name">{{
            vehicle.name
          }}</q-item-label>
        </q-item-section>
      </q-item>
    </q-list>
  </q-btn-dropdown>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';

const props = defineProps({
  chargePointId: {
    type: Number,
    required: true,
  },
  readonly: {
    type: Boolean,
    default: false,
  },
});

const mqttStore = useMqttStore();

const connectedVehicle = mqttStore.chargePointConnectedVehicleInfo(
  props.chargePointId,
);

const vehicles = computed(() => mqttStore.vehicleList);
</script>

<style scoped>
.flex-grow {
  flex-grow: 1;
}
</style>
