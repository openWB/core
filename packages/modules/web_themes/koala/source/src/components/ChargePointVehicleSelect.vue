<template>
  <div v-if="props.readonly" class="q-mx-sm">
    <q-icon name="directions_car" />
    {{ connectedVehicle?.name }}
  </div>
  <q-btn-dropdown
    v-else-if="isMobile"
    color="var(--q-text)"
    transition-show="scale"
    transition-hide="scale"
    transition-duration="500"
    size="md"
    dropdown-icon="none"
    cover
    outline
    class="no-drop-down-arrow"
    content-class="vehicle-select-dropdown-menu"
  >
    <template #label>
      <span class="block ellipsis" :title="connectedVehicle?.name">
        <q-icon name="directions_car" color="primary" />
        {{ connectedVehicle?.name }}
      </span>
    </template>
    <q-list>
      <template v-for="(vehicle, index) in vehicles" :key="vehicle.id">
        <q-item
          clickable
          v-close-popup
          @click="connectedVehicle = vehicle"
          :active="connectedVehicle?.id === vehicle.id"
          class="vehicle-item"
          :style="{
            '--vehicle-color':
              mqttStore.vehicleColor(vehicle.id) || 'var(--q-vehicle-stroke)',
          }"
        >
          <q-item-section class="text-center text-weight-bold">
            <q-item-label class="ellipsis" :title="vehicle.name">{{
              vehicle.name
            }}</q-item-label>
          </q-item-section>
        </q-item>
        <q-separator v-if="index < vehicles.length - 1" />
      </template>
    </q-list>
  </q-btn-dropdown>
  <q-btn-dropdown
    v-else
    color="grey"
    dense
    no-caps
    outline
    content-class="vehicle-select-dropdown-menu"
  >
    <template #label>
      <span class="ellipsis q-ml-xs" :title="connectedVehicle?.name">
        <q-icon name="directions_car" color="primary" />
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
        :active="connectedVehicle?.id === vehicle.id"
        @click="connectedVehicle = vehicle"
        class="vehicle-item vehicle-item--desktop"
        :style="{
          '--vehicle-color':
            mqttStore.vehicleColor(vehicle.id) || 'var(--q-vehicle-stroke)',
        }"
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
import { Platform } from 'quasar';
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

const isMobile = computed(() => Platform.is.mobile);

const mqttStore = useMqttStore();

const connectedVehicle = mqttStore.chargePointConnectedVehicleInfo(
  props.chargePointId,
);

const vehicles = computed(() => mqttStore.vehicleList);
</script>

<style scoped>
.no-drop-down-arrow :deep(.q-btn-dropdown__arrow-container) {
  width: 0;
  padding: 0;
  margin: 0;
}
.vehicle-select-dropdown-menu .q-item--active {
  color: var(--q-primary) !important;
}
.vehicle-item {
  position: relative;
}
.vehicle-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0.2rem;
  bottom: 0.2rem;
  width: 4px;
  border-radius: 2px;
  background: var(--vehicle-color, var(--q-vehicle-stroke));
}
/* Reduce default Quasar item left padding on desktop */
.vehicle-item--desktop {
  padding-left: 0.6rem;
}
</style>
