<template>
  <q-card class="full-height q-ma-sm q-pa-sm" style="max-width: 23em">
    <q-card-section>
      <div class="row items-center text-h6" style="font-weight: bold">
        {{ name }}
        <ChargePointLockIcon :charge-point-id="props.chargePointId" />
        <ChargePointStateIcon :charge-point-id="props.chargePointId" />
        <q-space />
        <q-icon name="settings" size="sm" @click="settings = true" />
      </div>
      <ChargePointFaultMessage :charge-point-id="props.chargePointId" />
      <ChargePointStateMessage :charge-point-id="props.chargePointId" />
      <ChargePointModeButtons :charge-point-id="props.chargePointId" />
      <div class="row q-mt-sm">
        <div class="q-pa-sm">
          <div class="text-subtitle2">Leistung</div>
          {{ power }}
        </div>
        <div class="q-pa-sm">
          <div class="text-subtitle2">geladen</div>
          {{ '0' }}
        </div>
      </div>
      <div class="row items-center q-mt-sm">
        <q-icon name="directions_car" size="sm" />
        <div class="q-mx-sm">{{ connectedVehicle }}</div>
        <q-icon
          :name="priority ? 'star' : 'star_border'"
          :color="priority ? 'yellow' : 'grey'"
          size="sm"
        />
      </div>
      <SliderQuasar class="q-mt-sm" :readonly="true" />
    </q-card-section>
  </q-card>

  <!-- //////////////////////  Settings popup dialog  //////////////////// -->
  <q-dialog v-model="settings" :backdrop-filter="'blur(4px)'">
    <q-card>
      <q-card-section>
        <div class="text-h6">Einstellungen {{ name }}</div>
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
          <ChargePointModeButtons :charge-point-id="props.chargePointId" />
        </div>
        <div class="row items-center q-ma-none q-pa-none no-wrap">
          <div class="text-subtitle2 q-mr-sm">Sperren</div>
          <div>
            <ChargePointLockIcon :charge-point-id="props.chargePointId" />
          </div>
        </div>

        <div class="row items-center q-ma-none q-pa-none no-wrap">
          <div class="text-subtitle2 q-mr-sm">Priorität</div>
          <div>
            <q-toggle
              v-model="priorityToggle"
              :color="priority ? 'positive' : 'negative'"
              :keep-color="true"
              checked-icon="star"
              unchecked-icon="star_border"
              size="lg"
            />
          </div>
        </div>
        <SliderQuasar class="q-mt-sm" :readonly="false" />
      </q-card-section>
      <q-card-actions align="right">
        <q-btn flat label="OK" color="primary" v-close-popup />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import SliderQuasar from './SliderQuasar.vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import ChargePointLockIcon from './ChargePointLockIcon.vue';
import ChargePointStateIcon from './ChargePointStateIcon.vue';
import ChargePointModeButtons from './ChargePointModeButtons.vue';
import ChargePointStateMessage from './ChargePointStateMessage.vue';
import ChargePointFaultMessage from './ChargePointFaultMessage.vue';

const props = defineProps<{
  chargePointId: number;
}>();

const mqttStore = useMqttStore();

// Begin dummy data
const settings = ref<boolean>(false);
const priority = computed(() => {
  return false;
});
const priorityToggle = ref<boolean>(false);
const connectedVehicle = ref<string>('Standard vehicle');
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
// End dummy data

const name = computed(() => mqttStore.chargePointName(props.chargePointId));

const power = computed(() =>
  mqttStore.chargePointPower(props.chargePointId, 'textValue'),
);
</script>
