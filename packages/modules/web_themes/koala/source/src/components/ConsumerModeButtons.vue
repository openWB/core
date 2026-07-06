<template>
  <div v-if="isMobile" class="row q-pt-md full-width">
    <q-btn-dropdown
      class="col"
      transition-show="scale"
      transition-hide="scale"
      transition-duration="500"
      color="primary"
      :label="currentModeLabel"
      size="md"
      dropdown-icon="none"
      cover
      push
    >
      <q-list>
        <template v-for="(mode, index) in chargeModes" :key="mode.value">
          <q-item
            clickable
            v-close-popup
            @click="consumerMode = mode.value"
            :active="consumerMode === mode.value"
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
  <q-btn-group v-else class="row col q-mt-sm" spread>
    <q-btn
      v-for="mode in chargeModes"
      :key="mode.value"
      :color="consumerMode === mode.value ? 'primary' : 'grey'"
      :label="mode.label"
      size="sm"
      @click="consumerMode = mode.value"
    />
  </q-btn-group>
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import { computed } from 'vue';
import { Platform } from 'quasar';
import { useChargeModes } from 'src/composables/useChargeModes';

const props = defineProps<{
  consumerId: number;
}>();

const isMobile = computed(() => Platform.is.mobile);
const { chargeModes } = useChargeModes();
const mqttStore = useMqttStore();

const consumerMode = mqttStore.consumerMode(props.consumerId);

const currentModeLabel = computed(
  () => chargeModes.find((mode) => mode.value === consumerMode.value)?.label,
);
</script>

<style scoped>
:deep(.q-btn-dropdown__arrow-container) {
  width: 0;
  padding: 0;
  margin: 0;
}
</style>
