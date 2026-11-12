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
        title="Speicher-Einstellungen öffnen"
        @click="showDialog = true"
      >
        <IconGear />
      </BaseIconButton>
    </div>

    <div
      class="status-box mb-2.5 min-h-24 px-3 py-2 text-xs"
      :class="faultState > 0 && faultMessage ? 'status-box-fault' : 'status-box-info'"
    >
      {{ faultState > 0 && faultMessage ? faultMessage : stateMessage || 'Kein Status verfügbar.' }}
    </div>

    <div class="flex gap-4 text-[13px]">
      <StatBlock
        label="Leistung"
        :value="formatKw(power)"
      />
      <StatBlock
        label="Geladen heute"
        :value="formatKwh(dailyImported)"
      />
      <StatBlock
        label="Entladen heute"
        :value="formatKwh(dailyExported)"
      />
      <StatBlock
        v-if="soc !== undefined"
        class="ml-auto"
        label="SoC"
        :value="`${Math.round(soc)} %`"
      />
    </div>

    <BatterySettings v-model="showDialog" />
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
import StatBlock from './StatBlock.vue'

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
// active-control status ("Hält SoC bei X%" etc.) is inherently per-battery - no aggregate
// equivalent exists, so the overview pseudo-card just falls back to the generic empty state
const stateMessage = computed(() => (isOverview.value ? '' : mqttStore.batteryInstanceStateMessage(props.batteryId)))
</script>
