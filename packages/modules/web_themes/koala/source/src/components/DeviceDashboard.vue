<template>
  <section class="device-dashboard" aria-label="Geräte-Dashboard">
    <article
      v-for="device in devices"
      :key="`${device.section}:${device.id}`"
      :data-device-type="device.section"
      :data-device-id="device.id"
      class="dashboard-device"
    >
      <ChargePointCard
        v-if="device.section === 'charge-points'"
        :charge-point-id="device.id"
      />
      <VehicleCard
        v-else-if="device.section === 'vehicles'"
        :vehicle-id="device.id"
      />
      <BatteryCard
        v-else-if="device.section === 'batteries'"
        :battery-id="device.id"
      />
      <ConsumerCard v-else :consumer-id="device.id" />
    </article>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import { useLocalDataStore } from 'src/stores/localData-store';
import { useDeviceSections } from './deviceSections';
import ChargePointCard from './ChargePointCard.vue';
import VehicleCard from './VehicleCard.vue';
import BatteryCard from './BatteryCard.vue';
import ConsumerCard from './ConsumerCard.vue';

const mqttStore = useMqttStore();
const localDataStore = useLocalDataStore();
const availableSections = useDeviceSections();
const devices = computed(() => {
  const ids = {
    'charge-points': mqttStore.chargePointIds,
    vehicles: mqttStore.vehicleList.map((vehicle) => vehicle.id),
    batteries: mqttStore.batteryIds,
    consumers: mqttStore.consumerIds,
  };
  return availableSections.value
    .filter((section) =>
      localDataStore.dashboardDeviceSections.includes(section.name),
    )
    .flatMap((section) =>
      ids[section.name].map((id) => ({
        id,
        section: section.name,
      })),
    );
});
</script>

<style scoped>
.device-dashboard {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 22em), 1fr));
  align-items: stretch;
  gap: var(--dashboard-gap, 12px);
  width: 100%;
  min-width: 0;
}
.dashboard-device {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.dashboard-device > :deep(.q-card) {
  flex: 1;
  width: 100%;
  max-width: 100%;
}
</style>
