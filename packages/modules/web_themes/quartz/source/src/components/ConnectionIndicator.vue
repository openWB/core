<template>
  <BaseIconButton
    v-if="showIcon"
    aria-label="Verbindungsstatus"
    :title="stateDisplay.tooltip"
  >
    <component
      :is="stateDisplay.icon"
      :class="[stateDisplay.colorClass, { 'animate-spin': connectionState === 'connecting' }]"
    />
  </BaseIconButton>

  <!-- no close affordance on purpose - this blocks interaction until the connection is actually
       back, same as koala's persistent q-dialog; dismissing it would just hide a real problem. -->
  <div
    v-if="showDialog"
    class="fixed inset-0 z-[80] flex items-center justify-center bg-[rgba(10,12,16,0.5)] px-4"
  >
    <div class="panel flex max-w-[360px] items-center gap-3 px-5 py-4">
      <component
        :is="stateDisplay.icon"
        :class="[stateDisplay.colorClass, { 'animate-spin': connectionState === 'connecting' }]"
        class="h-6 w-6 flex-none"
      />
      <p class="m-0 text-[14px] text-text">
        {{ stateDisplay.message }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'
import BaseIconButton from './BaseIconButton.vue'
import IconLink from './icons/IconLink.vue'
import IconLinkOff from './icons/IconLinkOff.vue'
import IconRefresh from './icons/IconRefresh.vue'

// matches koala's ConnectionIndicator.vue timings and copy - delay before showing the connecting
// dialog (avoids flicker on fast reconnects) and the grace period before warning the user the
// connection might really be down rather than just mid-reconnect.
const DIALOG_DELAY_MS = 1000
const GRACE_PERIOD_MS = 10000
const ICON_HIDE_AFTER_RECONNECT_MS = 5000

const mqttStore = useMqttStore()
const connected = computed(() => mqttStore.connected)

const dialogDelayPassed = ref(false)
const gracePeriodExpired = ref(false)
const showIcon = ref(false)
let dialogDelayTimer: ReturnType<typeof setTimeout> | undefined
let gracePeriodTimer: ReturnType<typeof setTimeout> | undefined
let iconHideTimer: ReturnType<typeof setTimeout> | undefined

const connectionState = computed(() => {
  if (connected.value) return 'connected'
  return gracePeriodExpired.value ? 'disconnected' : 'connecting'
})

const stateDisplay = computed(() => {
  switch (connectionState.value) {
    case 'connected':
      return { icon: IconLink, colorClass: 'text-pv', tooltip: 'Verbindung hergestellt', message: '' }
    case 'connecting':
      return {
        icon: IconRefresh,
        colorClass: 'text-muted',
        tooltip: 'Verbindung wird aufgebaut',
        message: 'Die Verbindung zur openWB wird hergestellt. Bitte warten...',
      }
    default:
      return {
        icon: IconLinkOff,
        colorClass: 'text-error',
        tooltip: 'Verbindung getrennt',
        message: 'Die Verbindung zur openWB ist unterbrochen. Es wird versucht, die Verbindung wieder herzustellen...',
      }
  }
})

const showDialog = computed(
  () => connectionState.value === 'disconnected' || (connectionState.value === 'connecting' && dialogDelayPassed.value),
)

function clearConnectingTimers(): void {
  clearTimeout(dialogDelayTimer)
  clearTimeout(gracePeriodTimer)
}

function startConnectingTimers(): void {
  clearConnectingTimers()
  dialogDelayPassed.value = false
  gracePeriodExpired.value = false
  dialogDelayTimer = setTimeout(() => {
    dialogDelayPassed.value = true
  }, DIALOG_DELAY_MS)
  gracePeriodTimer = setTimeout(() => {
    gracePeriodExpired.value = true
  }, GRACE_PERIOD_MS)
}

watch(
  connected,
  (newValue, oldValue) => {
    if (!newValue) {
      showIcon.value = true
      clearTimeout(iconHideTimer)
      startConnectingTimers()
    } else if (oldValue !== undefined) {
      clearConnectingTimers()
      dialogDelayPassed.value = false
      gracePeriodExpired.value = false
      clearTimeout(iconHideTimer)
      iconHideTimer = setTimeout(() => {
        showIcon.value = false
      }, ICON_HIDE_AFTER_RECONNECT_MS)
    }
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  clearConnectingTimers()
  clearTimeout(iconHideTimer)
})
</script>
