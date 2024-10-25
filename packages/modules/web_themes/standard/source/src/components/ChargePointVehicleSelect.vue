<template>
  <div v-if="props.readonly" class="q-mx-sm">
    {{ connectedVehicle?.name }}
  </div>
  <q-btn-dropdown
    v-else
    color="dark-page"
    :label="connectedVehicle?.name"
    text-color="light"
    flat
    size="sm"
    icon="directions_car"
    dense
    outline
    no-caps
    style="font-size: 1em; text-align: left"
  >
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
          <q-item-label>{{ vehicle.name }}</q-item-label>
        </q-item-section>
      </q-item>
    </q-list>
  </q-btn-dropdown>
</template>

<script setup lang="ts">
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

const vehicles = mqttStore.vehicleList();
</script>
