import { computed, onMounted, onUnmounted, ref, watchEffect } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'

const HIDE_STANDARD_VEHICLE_STORAGE_KEY = 'quartz-hide-standard-vehicle'
// module-level (not per-call) so Theme-Einstellungen and every independent useVehicles() caller
// (App.vue's Fahrzeuge grid, ChargePointCard.vue's vehicle selector) share the same setting -
// no Pinia/MQTT dependency here, so (unlike useChartSettings' lazy singleton) a plain top-level
// ref is safe at module-eval time
const hideStandardVehicle = ref(localStorage.getItem(HIDE_STANDARD_VEHICLE_STORAGE_KEY) === 'true')
watchEffect(() => {
  try {
    localStorage.setItem(HIDE_STANDARD_VEHICLE_STORAGE_KEY, String(hideStandardVehicle.value))
  } catch {
    // ignore storage errors (private browsing etc.)
  }
})

/** Subscribes the vehicle-list and cross-chargepoint connection-state feeds for as long as the caller is mounted. */
export function useVehicles() {
  const mqttStore = useMqttStore()

  onMounted(() => {
    mqttStore.subscribeVehicleList()
    mqttStore.subscribeVehicleConnectionState()
    mqttStore.subscribeLoadmanagementPrios()
  })
  onUnmounted(() => {
    mqttStore.unsubscribeVehicleList()
    mqttStore.unsubscribeVehicleConnectionState()
    mqttStore.unsubscribeLoadmanagementPrios()
  })

  // the reserved placeholder vehicle every install has - hidden from lists/selectors when the
  // user opts in via Theme-Einstellungen
  const vehicleList = computed(() =>
    hideStandardVehicle.value ? mqttStore.vehicleList.filter((v) => v.name !== 'Standard-Fahrzeug') : mqttStore.vehicleList,
  )

  // only vehicles whose /info has actually arrived - excludes ids that exist in /name but
  // never finished publishing (transitional/broken state)
  const vehicleIds = computed(() =>
    vehicleList.value.filter((v) => mqttStore.vehicleInfo(v.id) !== undefined).map((v) => v.id),
  )

  return { vehicleList, vehicleIds, hideStandardVehicle }
}
