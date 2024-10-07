import { boot } from 'quasar/wrappers';
import { useMqttStore } from 'src/stores/mqtt-store';

// more info on params: https://v2.quasar.dev/quasar-cli/boot-files
export default boot(() => {
  const mqttStore = useMqttStore();
  mqttStore.initialize();
});
