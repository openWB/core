<template>
  <div class="q-pt-md full-width" v-if="isMobile">
    <q-btn-dropdown
      transition-show="scale"
      transition-hide="scale"
      transition-duration="500"
      class="full-width"
      color="primary"
      :label="currentModeLabel"
      size="lg"
      dropdown-icon="none"
      cover
      push
    >
      <q-list>
        <template v-for="(mode, index) in chargeModes" :key="mode.value">
          <q-item
            clickable
            v-close-popup
            @click="chargeMode.value = mode.value"
            :active="chargeMode.value === mode.value"
            active-class="bg-primary text-white"
          >
            <q-item-section class="text-center text-weight-bold">
              <q-item-label>{{ mode.label.toLocaleUpperCase() }}</q-item-label>
            </q-item-section>
          </q-item>
          <q-separator v-if="index < chargeModes.length - 1" />
        </template>
      </q-list>
    </q-btn-dropdown>
  </div>
  <div v-else>
    <q-btn-group spread class="q-mt-sm">
      <q-btn
        v-for="mode in chargeModes.slice(0, 3)"
        :key="mode.value"
        :color="chargeMode.value === mode.value ? 'primary' : 'grey'"
        :label="mode.label"
        size="sm"
        @click="chargeMode.value = mode.value"
      />
    </q-btn-group>
    <q-btn-group spread>
      <q-btn
        v-for="mode in chargeModes.slice(3, 6)"
        :key="mode.value"
        :color="chargeMode.value === mode.value ? 'primary' : 'grey'"
        :label="mode.label"
        size="sm"
        @click="chargeMode.value = mode.value"
      />
    </q-btn-group>
  </div>
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import { computed } from 'vue';
import { Platform } from 'quasar';
import { useChargeModes } from 'src/composables/useChargeModes';

const props = defineProps<{
  chargePointId: number;
}>();

const isMobile = computed(() => Platform.is.mobile);
const { chargeModes } = useChargeModes();
const mqttStore = useMqttStore();

const chargeMode = computed(() =>
  mqttStore.chargePointConnectedVehicleChargeMode(props.chargePointId),
);

const currentModeLabel = computed(
  () =>
    chargeModes.find((mode) => mode.value === chargeMode.value.value)?.label,
);
</script>

<style scoped>
:deep(.q-btn-dropdown__arrow-container) {
  width: 0;
  padding: 0;
}

.flex-grow {
  flex-grow: 1;
}

.q-btn-group:first-of-type .q-btn:first-child {
  border-top-left-radius: 3px;
  border-bottom-left-radius: 0;
}
.q-btn-group:first-of-type .q-btn:last-child {
  border-top-right-radius: 3px;
  border-bottom-right-radius: 0;
}
.q-btn-group:last-of-type .q-btn:first-child {
  border-top-left-radius: 0;
  border-bottom-left-radius: 3px;
}
.q-btn-group:last-of-type .q-btn:last-child {
  border-top-right-radius: 0;
  border-bottom-right-radius: 3px;
}
</style>
