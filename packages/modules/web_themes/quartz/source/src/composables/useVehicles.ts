import { computed, onMounted, onUnmounted, ref, watchEffect } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'
import { readStorage, writeStorage } from '@/utils/storage'

const HIDE_STANDARD_VEHICLE_STORAGE_KEY = 'quartz-hide-standard-vehicle'
// module-level so every caller shares the setting
const hideStandardVehicle = ref(readStorage(HIDE_STANDARD_VEHICLE_STORAGE_KEY) === 'true')
watchEffect(() => writeStorage(HIDE_STANDARD_VEHICLE_STORAGE_KEY, String(hideStandardVehicle.value)))

export function useVehicles() {
  const mqttStore = useMqttStore()

  onMounted(() => {
    mqttStore.subscribeVehicleList()
    mqttStore.subscribeVehicleConnectionState()
  })
  onUnmounted(() => {
    mqttStore.unsubscribeVehicleList()
    mqttStore.unsubscribeVehicleConnectionState()
  })

  // vehicle 0 is the placeholder every install has; matched by id because its name can be changed
  const vehicleList = computed(() =>
    hideStandardVehicle.value ? mqttStore.vehicleList.filter((v) => v.id !== 0) : mqttStore.vehicleList,
  )

  // only vehicles whose /info has arrived
  const vehicleIds = computed(() =>
    vehicleList.value.filter((v) => mqttStore.vehicleInfo(v.id) !== undefined).map((v) => v.id),
  )

  return { vehicleList, vehicleIds, hideStandardVehicle }
}
