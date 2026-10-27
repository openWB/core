<template>
  <div class="panel px-4 py-3">
    <div class="mb-2.5 flex items-center gap-2">
      <IconSun class="text-pv" />
      <span class="text-[14px] font-bold">{{ name }}</span>
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
          Eingespeist heute
        </div>
        <div class="font-bold">
          {{ formatKwh(dailyExported) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'
import { formatKw, formatKwh } from '@/utils/format'
import IconSun from './icons/IconSun.vue'

const props = defineProps<{ inverterId: number }>()
const mqttStore = useMqttStore()

const name = computed(() => mqttStore.inverterName(props.inverterId))
const power = computed(() => mqttStore.inverterInstancePower(props.inverterId))
const dailyExported = computed(() => mqttStore.inverterInstanceDailyExported(props.inverterId))
const faultState = computed(() => mqttStore.inverterInstanceFaultState(props.inverterId))
const faultMessage = computed(() => mqttStore.inverterInstanceFaultMessage(props.inverterId))
</script>
