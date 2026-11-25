import { computed } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';

const deviceSections = [
  { name: 'charge-points', label: 'Ladepunkte', icon: 'ev_station' },
  { name: 'vehicles', label: 'Fahrzeuge', icon: 'directions_car' },
  { name: 'batteries', label: 'Speicher', icon: 'battery_full' },
  { name: 'consumers', label: 'Verbraucher', icon: 'power' },
] as const;

export function useDeviceSections() {
  const mqttStore = useMqttStore();
  return computed(() =>
    deviceSections.filter((section) => {
      switch (section.name) {
        case 'charge-points':
          return mqttStore.chargePointIds.length > 0;
        case 'vehicles':
          return mqttStore.vehicleList.length > 0;
        case 'batteries':
          return mqttStore.batteryConfigured && mqttStore.batteryIds.length > 0;
        case 'consumers':
          return mqttStore.consumerIds.length > 0;
      }
    }),
  );
}
