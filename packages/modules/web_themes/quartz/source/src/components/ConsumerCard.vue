<template>
  <div class="panel px-4 py-3">
    <div class="mb-2.5 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <IconConsumer class="text-consumer" />
        <span class="text-[14px] font-bold">{{ name }}</span>
      </div>
      <div class="flex items-center gap-1">
        <BaseIconButton
          v-if="showControls"
          aria-label="Verbraucher-Einstellungen öffnen"
          @click="showSettings = true"
        >
          <IconGear />
        </BaseIconButton>
        <span
          v-if="priority !== undefined"
          class="whitespace-nowrap rounded-full px-[9px] py-[3px] text-[11px] font-bold badge-muted"
        >Prio {{ priority }}</span>
        <span :class="['whitespace-nowrap rounded-full px-[9px] py-[3px] text-[11px] font-bold', stateBadgeClass]">{{ stateBadgeText }}</span>
      </div>
    </div>

    <ConsumerSettings
      v-if="showControls"
      v-model="showSettings"
      :consumer-id="props.consumerId"
      :name="name"
    />

    <p
      v-if="faultState > 0 && faultMessage"
      class="mt-0 mb-2.5 text-xs text-grid"
    >
      {{ faultMessage }}
    </p>
    <p
      v-else-if="stateMessage"
      class="mt-0 mb-2.5 text-xs text-muted"
    >
      {{ stateMessage }}
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
          Laufzeit
        </div>
        <div class="font-bold">
          {{ formatRuntime(onTime) }}
        </div>
      </div>
      <div>
        <div class="text-muted">
          Verbraucht heute
        </div>
        <div class="font-bold">
          {{ formatKwh(dailyImported) }}
        </div>
      </div>
    </div>

    <div
      v-if="temperatures.length > 0"
      class="mt-3 flex gap-4 text-[13px]"
    >
      <div
        v-for="(temp, idx) in temperatures"
        :key="idx"
      >
        <div class="text-muted">
          {{ temperatures.length > 1 ? `Temperatur ${idx + 1}` : 'Temperatur' }}
        </div>
        <div class="font-bold">
          {{ temp.toLocaleString(undefined, { maximumFractionDigits: 1 }) }}&nbsp;°C
        </div>
      </div>
    </div>

    <BaseTabGroup
      v-if="showControls"
      dense
      class="mt-3"
      :model-value="mode"
      :options="chargeModes"
      @update="mqttStore.setConsumerMode(props.consumerId, $event)"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'
import { formatKw, formatKwh, formatRuntime } from '@/utils/format'
import { chargeModes } from '@/utils/chargeModes'
import IconConsumer from './icons/IconConsumer.vue'
import IconGear from './icons/IconGear.vue'
import BaseIconButton from './BaseIconButton.vue'
import BaseTabGroup from './BaseTabGroup.vue'
import ConsumerSettings from './ConsumerSettings.vue'

const props = defineProps<{ consumerId: number }>()
const mqttStore = useMqttStore()

const showSettings = ref(false)

const name = computed(() => mqttStore.consumerName(props.consumerId))
const power = computed(() => mqttStore.consumerInstancePower(props.consumerId))
const dailyImported = computed(() => mqttStore.consumerInstanceDailyImported(props.consumerId))
const onTime = computed(() => mqttStore.consumerOnTime(props.consumerId))
const temperatures = computed(() => mqttStore.consumerTemperatures(props.consumerId))
const faultState = computed(() => mqttStore.consumerInstanceFaultState(props.consumerId))
const faultMessage = computed(() => mqttStore.consumerInstanceFaultMessage(props.consumerId))
const stateMessage = computed(() => mqttStore.consumerInstanceStateMessage(props.consumerId))
const plugState = computed(() => mqttStore.consumerPlugState(props.consumerId))
const chargeState = computed(() => mqttStore.consumerChargeState(props.consumerId))
const priority = computed(() => mqttStore.consumerPriority(props.consumerId))
const mode = computed(() => mqttStore.consumerMode(props.consumerId))

// meter-only/self-controlled consumers can't be switched by openWB - nothing to configure
const showControls = computed(() => {
  const usageType = mqttStore.consumerUsageType(props.consumerId)
  return usageType !== 'meter_only' && usageType !== 'self_controlled'
})

const stateBadgeText = computed(() => {
  if (chargeState.value) return 'An'
  if (plugState.value) return 'Bereit'
  return 'Aus'
})
const stateBadgeClass = computed(() => {
  if (chargeState.value) return 'badge-ok'
  if (plugState.value) return 'badge-wait'
  return 'badge-muted'
})
</script>
