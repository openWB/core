<template>
  <div class="panel px-4 py-3">
    <div class="mb-2.5 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <IconBattery class="text-battery" />
        <span class="text-[14px] font-bold">{{ name }}</span>
      </div>
      <BaseIconButton
        v-if="showSettings"
        aria-label="Speicher-Einstellungen öffnen"
        @click="showDialog = true"
      >
        <IconGear />
      </BaseIconButton>
    </div>

    <p
      v-if="faultState > 0 && faultMessage"
      class="mt-0 mb-2.5 text-xs text-grid"
    >
      {{ faultMessage }}
    </p>

    <div class="flex gap-4 text-[13px]">
      <div>
        <div class="text-muted">
          Leistung
        </div>
        <div class="font-bold">
          {{ formatKw(power) }}
        </div>
      </div>
      <div>
        <div class="text-muted">
          Geladen heute
        </div>
        <div class="font-bold">
          {{ formatKwh(dailyImported) }}
        </div>
      </div>
      <div>
        <div class="text-muted">
          Entladen heute
        </div>
        <div class="font-bold">
          {{ formatKwh(dailyExported) }}
        </div>
      </div>
      <div
        v-if="soc !== undefined"
        class="ml-auto"
      >
        <div class="text-muted">
          SoC
        </div>
        <div class="font-bold">
          {{ Math.round(soc) }}&nbsp;%
        </div>
      </div>
    </div>

    <BatterySettings
      v-model="showDialog"
      :name="name"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'
import { formatKw, formatKwh } from '@/utils/format'
import IconBattery from './icons/IconBattery.vue'
import IconGear from './icons/IconGear.vue'
import BaseIconButton from './BaseIconButton.vue'
import BatterySettings from './BatterySettings.vue'

const props = defineProps<{ batteryId: number }>()
const mqttStore = useMqttStore()

const isOverview = computed(() => props.batteryId === -1)
const showSettings = computed(() => isOverview.value || mqttStore.batteryIds.length === 1)
const showDialog = ref(false)

const name = computed(() => (isOverview.value ? 'Speicher Übersicht' : mqttStore.batteryName(props.batteryId)))
const soc = computed(() => (isOverview.value ? mqttStore.batterySoc : mqttStore.batteryInstanceSoc(props.batteryId)))
const power = computed(() => (isOverview.value ? mqttStore.batteryPower : mqttStore.batteryInstancePower(props.batteryId)))
const dailyImported = computed(() =>
  isOverview.value ? mqttStore.batteryDailyImportedTotal() : mqttStore.batteryInstanceDailyImported(props.batteryId),
)
const dailyExported = computed(() =>
  isOverview.value ? mqttStore.batteryDailyExportedTotal() : mqttStore.batteryInstanceDailyExported(props.batteryId),
)
const faultState = computed(() =>
  isOverview.value ? mqttStore.batteryFaultStateTotal() : mqttStore.batteryInstanceFaultState(props.batteryId),
)
const faultMessage = computed(() =>
  isOverview.value ? mqttStore.batteryFaultMessageTotal() : mqttStore.batteryInstanceFaultMessage(props.batteryId),
)
</script>
