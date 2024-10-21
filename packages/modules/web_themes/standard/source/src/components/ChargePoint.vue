<template>
  <q-card class="full-height" v-if="chargePoint" style="max-width: 23em">
    <q-card-section>
      <div class="row items-center text-h6" style="font-weight: bold">
        {{ chargePoint.name }}
        <q-icon
          :name="chargePoint.locked ? 'lock' : 'lock_open'"
          size="sm"
          :color="chargePoint.locked ? 'red' : 'green'"
          @click="toggleLock(chargePoint.id, chargePoint.locked)"
          style="cursor: pointer"
          class="q-ml-sm"
        />
        <q-icon
          :name="chargePoint.state ? 'power' : 'power_off'"
          size="sm"
          :color="chargePoint.state ? 'green' : 'red'"
        />
        <q-space />
        <q-icon name="settings" size="sm" @click="settings = true" />
      </div>
      <q-banner class="q-mt-md q-pa-sm bg-primary text-white" rounded>
        {{ chargePoint.message }}
      </q-banner>
      <q-btn-group push rounded class="q-mt-md">
        <q-btn
          v-for="mode in chargeModes"
          :key="mode.value"
          :flat="selectedButton !== mode.value"
          :outline="selectedButton === mode.value"
          :glossy="selectedButton === mode.value"
          :label="mode.label"
          :color="mode.color"
          size="xs"
          @click="setChargeMode(mode.value)"
        />
      </q-btn-group>
      <div class="row q-mt-sm">
        <div class="q-pa-sm">
          <div class="text-subtitle2">Leistung</div>
          {{ chargePoint.power }}
        </div>
        <div class="q-pa-sm">
          <div class="text-subtitle2">geladen</div>
          {{ '0' }}
        </div>
      </div>
      <div class="row items-center q-mt-sm">
        <q-icon name="directions_car" size="sm" />
        <div class="q-mx-sm">{{ chargePoint.conectedVehicle }}</div>
        <q-icon
          :name="chargePoint.priority ? 'star' : 'star_border'"
          :color="chargePoint.priority ? 'yellow' : 'grey'"
          size="sm"
        />
      </div>
      <SliderQuasar class="q-mt-sm" :thumb-size="'0px'" :move="true" />
    </q-card-section>
  </q-card>

  <!-- //////////////////////  Settings popup dialog  //////////////////// -->
  <q-dialog
    v-if="chargePoint"
    v-model="settings"
    :backdrop-filter="'blur(4px)'"
  >
    <q-card>
      <q-card-section>
        <div class="text-h6">Einstellungen {{ chargePoint?.name }}</div>
      </q-card-section>

      <q-card-section class="q-pt-none">
        <div class="row items-center q-ma-none q-pa-none">
          <div>
            <div class="text-subtitle2 q-mr-sm">Fahrzeug</div>
          </div>
          <q-btn-dropdown
            color="dark-page"
            :label="selectedVehicle"
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
                v-for="(vehicle, index) in vehicles"
                :key="index"
                clickable
                v-close-popup
                dense
                @click="selectVehicle(vehicle.value)"
              >
                <q-item-section>
                  <q-item-label>{{ vehicle.value }}</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </q-btn-dropdown>
        </div>
        <div class="row items-center q-ma-none q-pa-none no-wrap">
          <q-btn-group push rounded class="q-mt-md">
            <q-btn
              v-for="mode in chargeModes"
              :key="mode.value"
              :flat="selectedButton !== mode.value"
              :outline="selectedButton === mode.value"
              :glossy="selectedButton === mode.value"
              :label="mode.label"
              :color="mode.color"
              size="xs"
              @click="setChargeMode(mode.value)"
            />
          </q-btn-group>
        </div>
        <div class="row items-center q-ma-none q-pa-none no-wrap">
          <div class="text-subtitle2 q-mr-sm">Sperren</div>
          <div>
            <q-toggle
              v-model="chargePoint.locked"
              :color="chargePoint.locked ? 'negative' : 'positive'"
              :keep-color="true"
              checked-icon="lock"
              unchecked-icon="lock_open"
              size="lg"
              @update:model-value="
                (value: boolean) => toggleLock(props.chargePointId, !value)
              "
            />
          </div>
        </div>

        <div class="row items-center q-ma-none q-pa-none no-wrap">
          <div class="text-subtitle2 q-mr-sm">Priorität</div>
          <div>
            <q-toggle
              v-model="priorityToggle"
              :color="chargePoint.priority ? 'positive' : 'negative'"
              :keep-color="true"
              checked-icon="star"
              unchecked-icon="star_border"
              size="lg"
            />
          </div>
        </div>
        <SliderQuasar
          class="q-mt-sm"
          :thumb-size="'37px'"
          :move="false"
        ></SliderQuasar>
      </q-card-section>
      <q-card-actions align="right">
        <q-btn flat label="OK" color="primary" v-close-popup />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import SliderQuasar from './SliderQuasar.vue';
import { useMqttStore } from 'src/stores/mqtt-store';

const props = defineProps<{
  chargePointId: number;
}>();

const mqttStore = useMqttStore();

const settings = ref<boolean>(false);
const lockToggle = ref<boolean>(false);
const priorityToggle = ref<boolean>(false);

const topicsToSubscribe = <string[]>[
  'openWB/chargepoint/+/config',
  'openWB/chargepoint/+/set/manual_lock',
  'openWB/chargepoint/+/get/power',
  'openWB/chargepoint/+/get/state_str',
  'openWB/chargepoint/+/get/plug_state',
  'openWB/chargepoint/+/get/conected_vehicle',
  'openWB/chargepoint/+/get/connected_vehicle/config',
  'openWB/chargepoint/+/get/connected_vehicle/config',
  'openWB/chargepoint/+/get/connected_vehicle/info',
  'openWB/vehicle/template/charge_template/0',
];

const chargePoint = computed(() =>
  mqttStore.getChargePointDetails(props.chargePointId),
);

// Sync lock state with the charge point details
watch(chargePoint, (newVal) => {
  if (newVal) {
    lockToggle.value = newVal.locked;
    priorityToggle.value = newVal.priority;
  }
});

const selectedButton = computed(() => mqttStore.getChargeMode);

const chargeModes = [
  { value: 'sofort', label: 'Sofort', color: 'negative' },
  { value: 'pv', label: 'PV', color: 'positive' },
  { value: 'scheduled', label: 'Zeil', color: 'primary' },
  { value: 'standby', label: 'Standby', color: 'warning' },
  { value: 'stop', label: 'Stop', color: 'light' },
];

const vehicles = [
  { value: 'Standard vehicle' },
  { value: 'Tesla model 3' },
  { value: 'Tesla model Y' },
  { value: 'MG4' },
  { value: 'BMW i3' },
];

const selectedVehicle = ref<string>('Standard vehicle');

const selectVehicle = (vehicle: string) => {
  selectedVehicle.value = vehicle;
};

const toggleLock = (chargePointId: number, currentLockState: boolean) => {
  const topic = `openWB/chargepoint/${chargePointId}/set/manual_lock`;
  const newLockState = !currentLockState;
  //lockToggle.value = newLockState;
  mqttStore.updateTopic(topic, newLockState);
};

const setChargeMode = (mode: string) => {
  mqttStore.setChargeMode(mode);
};

onMounted(() => {
  mqttStore.subscribe(topicsToSubscribe);
});
</script>
