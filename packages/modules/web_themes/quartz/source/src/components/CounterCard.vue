<template>
  <div class="panel px-4 py-3">
    <div class="mb-2.5 flex items-center gap-2">
      <IconCounter class="text-grid" />
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
          Bezogen heute
        </div>
        <div class="font-bold">
          {{ formatKwh(dailyImported) }}
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
import IconCounter from './icons/IconCounter.vue'

const props = defineProps<{ counterId: number }>()
const mqttStore = useMqttStore()

const name = computed(() => mqttStore.counterName(props.counterId))
const power = computed(() => mqttStore.counterInstancePower(props.counterId))
const dailyImported = computed(() => mqttStore.counterInstanceDailyImported(props.counterId))
const dailyExported = computed(() => mqttStore.counterInstanceDailyExported(props.counterId))
const faultState = computed(() => mqttStore.counterInstanceFaultState(props.counterId))
const faultMessage = computed(() => mqttStore.counterInstanceFaultMessage(props.counterId))
</script>
