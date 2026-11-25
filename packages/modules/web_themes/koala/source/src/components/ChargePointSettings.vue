<template>
  <q-dialog
    v-model="visible"
    :maximized="isSmallScreen"
    :backdrop-filter="isSmallScreen ? '' : 'blur(4px)'"
    :persistent="localDataStore.desktopOverview && saving"
  >
    <q-card
      :class="{ 'dashboard-charge-point-settings': localDataStore.desktopOverview }"
    >
      <q-card-section>
        <template v-if="localDataStore.desktopOverview">
          <div
            class="row no-wrap items-center justify-between settings-header-actions"
          >
            <q-btn
              icon="close"
              flat
              round
              dense
              class="settings-header-action"
              aria-label="Schließen"
              :disable="saving"
              @click="visible = false"
            />
            <q-btn
              icon="check"
              color="primary"
              flat
              round
              dense
              class="settings-header-action"
              aria-label="Änderungen übernehmen"
              :loading="saving"
              @click="applyChanges"
            />
          </div>
          <div class="text-h6 settings-header-name q-mt-sm" :title="name">
            {{ name }}
          </div>
        </template>
        <div v-else class="row no-wrap">
          <div class="text-h6 q-pr-sm">Einstellungen:</div>
          <div class="text-h6 ellipsis" :title="name">{{ name }}</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </div>
      </q-card-section>
      <q-separator />
      <q-card-section :inert="saving || undefined">
        <div class="row items-center justify-between">
          <div class="text-subtitle2">Ladepunkt sperren</div>
          <ChargePointLock :charge-point-id="props.chargePointId" dense />
        </div>
        <q-separator class="q-mt-sm" />
        <div class="row items-center q-mt-sm">
          <div class="col-auto text-subtitle2 q-mr-sm">Fahrzeug</div>
          <div class="col">
            <ChargePointVehicleSelect
              class="full-width"
              :charge-point-id="props.chargePointId"
              :readonly="false"
            />
          </div>
        </div>
        <q-separator class="q-mt-sm" />
        <div class="row items-center no-wrap">
          <ChargePointModeButtons :charge-point-id="props.chargePointId" />
        </div>
        <!-- ///////////////// Instant charge settings /////////////////// -->
        <div v-if="chargeMode.value === 'instant_charging'">
          <ChargePointInstantSettings :charge-point-id="props.chargePointId" />
        </div>
        <!-- ///////////////// Pv charge settings /////////////////// -->
        <div v-if="chargeMode.value === 'pv_charging'">
          <ChargePointPvSettings :charge-point-id="props.chargePointId" />
        </div>
        <!-- ///////////////// Eco charge settings /////////////////// -->
        <div v-if="chargeMode.value === 'eco_charging'">
          <ChargePointEcoSettings :charge-point-id="props.chargePointId" />
        </div>
        <!-- /////////////////  scheduled charging settings /////////////////// -->
        <div v-if="chargeMode.value === 'scheduled_charging'">
          <ChargePointScheduledSettings
            :charge-point-id="props.chargePointId"
          />
        </div>
        <!-- /////////////////  time charging settings /////////////////// -->
        <div v-if="chargeMode.value !== 'stop'">
          <q-separator class="q-my-sm" />
          <ChargePointTimeChargingSettings
            :charge-point-id="props.chargePointId"
          />
        </div>
      </q-card-section>
      <q-dialog v-model="confirmClose" persistent>
        <q-card class="settings-discard-dialog">
          <q-card-section class="text-h6">Änderungen verwerfen?</q-card-section>
          <q-card-actions vertical class="q-pa-md q-gutter-y-sm">
            <q-btn
              label="Änderungen verwerfen"
              outline
              no-caps
              :disable="saving"
              @click="discardChanges"
            />
            <q-btn
              label="Änderungen übernehmen"
              color="primary"
              unelevated
              no-caps
              :loading="saving"
              @click="applyChanges"
            />
          </q-card-actions>
        </q-card>
      </q-dialog>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { Screen, QDialog, useQuasar } from 'quasar';
import {
  createPinia,
  defineStore,
  disposePinia,
  getActivePinia,
  setActivePinia,
} from 'pinia';
import {
  useMqttStore,
  mqttStoreSetup,
  settingsMqttStoreKey,
} from 'src/stores/mqtt-store';
import { createMqttSettingsDraft } from 'src/stores/mqtt-settings-draft';
import { useLocalDataStore } from 'src/stores/localData-store';
import { computed, onBeforeUnmount, provide, ref, watch } from 'vue';
import ChargePointInstantSettings from './ChargePointInstantSettings.vue';
import ChargePointPvSettings from './ChargePointPvSettings.vue';
import ChargePointEcoSettings from './ChargePointEcoSettings.vue';
import ChargePointScheduledSettings from './ChargePointScheduledSettings.vue';
import ChargePointTimeChargingSettings from './ChargePointTimeChargingSettings.vue';
import ChargePointLock from './ChargePointLock.vue';
import ChargePointModeButtons from './ChargePointModeButtons.vue';
import ChargePointVehicleSelect from './ChargePointVehicleSelect.vue';

const mqttStore = useMqttStore();
const localDataStore = useLocalDataStore();
const $q = useQuasar();
const draft = createMqttSettingsDraft(mqttStore);
const livePinia = getActivePinia();
const draftPinia = createPinia();
const draftStore = defineStore('mqtt', () => mqttStoreSetup(draft.transport))(
  draftPinia,
);
setActivePinia(livePinia);
provide(
  settingsMqttStoreKey,
  computed(() => (localDataStore.desktopOverview ? draftStore : mqttStore)),
);
onBeforeUnmount(() => disposePinia(draftPinia));
const saving = ref(false);
const confirmClose = ref(false);

const props = defineProps<{
  chargePointId: number;
  modelValue: boolean;
}>();

const emit = defineEmits<{
  'update:model-value': [value: boolean];
}>();

const isSmallScreen = computed(() => Screen.lt.sm);

const tempValue = ref<boolean>(props.modelValue);

watch(
  () => props.modelValue,
  (value) => {
    if (value) draft.reset();
    if (!value) confirmClose.value = false;
    tempValue.value = value;
  },
);

const visible = computed({
  get: () => tempValue.value,
  set: (value) => {
    if (!value && localDataStore.desktopOverview) {
      if (!saving.value) confirmClose.value = true;
      return;
    }
    tempValue.value = value;
    emit('update:model-value', value);
  },
});

const name = computed(() => mqttStore.chargePointName(props.chargePointId));

const chargeMode = computed(() =>
  (localDataStore.desktopOverview
    ? draftStore
    : mqttStore
  ).chargePointConnectedVehicleChargeMode(props.chargePointId),
);

function closeDialog() {
  confirmClose.value = false;
  tempValue.value = false;
  emit('update:model-value', false);
}

function discardChanges() {
  draft.reset();
  closeDialog();
}

async function applyChanges() {
  if (saving.value) return;
  saving.value = true;
  try {
    await draft.apply();
    closeDialog();
    $q.notify({ type: 'positive', message: 'Änderungen wurden übernommen.' });
  } catch (error) {
    $q.notify({
      type: 'negative',
      message:
        error instanceof Error
          ? error.message
          : 'Die Änderungen konnten nicht übernommen werden.',
    });
  } finally {
    saving.value = false;
  }
}
</script>

<style scoped>
.dashboard-charge-point-settings {
  width: 680px;
  min-width: min(600px, calc(100vw - 48px));
  max-width: calc(100vw - 48px);
}
.settings-header-actions {
  /* Align the icons themselves with the content edges, including without hover. */
  margin-inline: -6px;
}
.settings-header-action {
  flex: 0 0 36px;
  width: 36px;
  min-width: 36px;
  max-width: 36px;
  height: 36px;
  min-height: 36px;
  max-height: 36px;
  border-radius: 50%;
}
.settings-header-action :deep(.q-icon) {
  width: 24px;
  height: 24px;
  font-size: 24px;
  line-height: 1;
}
.settings-header-name {
  overflow-wrap: anywhere;
}
.settings-discard-dialog {
  width: 400px;
  max-width: calc(100vw - 32px);
}
@media (max-width: 599px) {
  .dashboard-charge-point-settings {
    width: 100%;
    min-width: 0;
    max-width: 100%;
  }
}
</style>
