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
          title="Verbraucher-Einstellungen öffnen"
          @click="showSettings = true"
        >
          <IconGear />
        </BaseIconButton>
        <span
          v-if="priority !== undefined"
          class="badge badge-muted"
        >Prio {{ priority }}</span>
        <span :class="['badge', stateBadgeClass]">{{ stateBadgeText }}</span>
      </div>
    </div>

    <ConsumerSettings
      v-if="showControls"
      v-model="showSettings"
      :consumer-id="props.consumerId"
      :name="name"
    />

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
        label="Laufzeit"
        :value="formatRuntime(onTime)"
      />
      <StatBlock
        label="Verbrauch heute"
        :value="formatKwh(dailyImported)"
      />
    </div>

    <div
      v-if="temperatures.length > 0"
      class="mt-3 flex gap-4 text-[13px]"
    >
      <StatBlock
        v-for="(temp, idx) in temperatures"
        :key="idx"
        :label="temperatures.length > 1 ? `Temperatur ${idx + 1}` : 'Temperatur'"
        :value="`${temp.toLocaleString(undefined, { maximumFractionDigits: 1 })} °C`"
      />
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
import { stateBadgeClass as stateBadgeClassFor } from '@/utils/badge'
import IconConsumer from './icons/IconConsumer.vue'
import IconGear from './icons/IconGear.vue'
import BaseIconButton from './BaseIconButton.vue'
import BaseTabGroup from './BaseTabGroup.vue'
import ConsumerSettings from './ConsumerSettings.vue'
import StatBlock from './StatBlock.vue'

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
const stateBadgeClass = computed(() => stateBadgeClassFor(chargeState.value, plugState.value))
</script>
