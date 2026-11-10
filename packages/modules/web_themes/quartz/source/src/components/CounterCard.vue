<template>
  <div class="panel px-4 py-3">
    <div class="mb-2.5 flex items-center gap-2">
      <IconCounter class="text-grid" />
      <span class="text-[14px] font-bold">{{ name }}</span>
    </div>

    <FaultMessage
      :fault-state="faultState"
      :fault-message="faultMessage"
    />

    <div class="flex gap-4 text-[13px]">
      <StatBlock
        label="Leistung"
        :value="formatKw(power)"
      />
      <StatBlock
        label="Bezogen heute"
        :value="formatKwh(dailyImported)"
      />
      <StatBlock
        label="Eingespeist heute"
        :value="formatKwh(dailyExported)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'
import { formatKw, formatKwh } from '@/utils/format'
import IconCounter from './icons/IconCounter.vue'
import StatBlock from './StatBlock.vue'
import FaultMessage from './FaultMessage.vue'

const props = defineProps<{ counterId: number }>()
const mqttStore = useMqttStore()

const name = computed(() => mqttStore.counterName(props.counterId))
const power = computed(() => mqttStore.counterInstancePower(props.counterId))
const dailyImported = computed(() => mqttStore.counterInstanceDailyImported(props.counterId))
const dailyExported = computed(() => mqttStore.counterInstanceDailyExported(props.counterId))
const faultState = computed(() => mqttStore.counterInstanceFaultState(props.counterId))
const faultMessage = computed(() => mqttStore.counterInstanceFaultMessage(props.counterId))
</script>
