<template>
  <BasePopover
    v-model="showSocEditor"
    panel-class="top-[calc(100%_+_8px)] right-0 flex w-55 flex-col gap-2.5 p-3"
  >
    <template #trigger>
      <BaseIconButton
        size="sm"
        aria-label="SoC manuell eingeben"
        title="SoC manuell eingeben"
        @click="openSocEditor"
      >
        <IconPencil />
      </BaseIconButton>
    </template>
    <div class="settings-group-label text-center">
      SoC {{ vehicleName }}
    </div>
    <div class="flex items-center justify-center gap-2 text-[13px]">
      <BaseIconButton
        aria-label="SoC verringern"
        title="SoC verringern"
        @click="socInputValue = Math.max(0, socInputValue - 1)"
      >
        &minus;
      </BaseIconButton>
      <input
        v-model.number="socInputValue"
        type="number"
        min="0"
        max="100"
        class="w-14 rounded-[6px] border border-border bg-bg p-1 text-center text-text"
      >
      <span>%</span>
      <BaseIconButton
        aria-label="SoC erhöhen"
        title="SoC erhöhen"
        @click="socInputValue = Math.min(100, socInputValue + 1)"
      >
        +
      </BaseIconButton>
    </div>
    <input
      v-model.number="socInputValue"
      type="range"
      min="0"
      max="100"
      class="range-slider"
    >
    <div class="flex justify-end gap-2">
      <BaseButton @click="showSocEditor = false">
        Abbrechen
      </BaseButton>
      <BaseButton
        variant="primary"
        @click="confirmSoc"
      >
        Übernehmen
      </BaseButton>
    </div>
  </BasePopover>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'
import IconPencil from './icons/IconPencil.vue'
import BaseIconButton from './BaseIconButton.vue'
import BaseButton from './BaseButton.vue'
import BasePopover from './BasePopover.vue'

const props = defineProps<{ vehicleId: number; vehicleName: string; chargePointId?: number }>()
const mqttStore = useMqttStore()

const showSocEditor = ref(false)
const socInputValue = ref(0)

function openSocEditor(): void {
  socInputValue.value = Math.round(mqttStore.vehicleManualSoc(props.vehicleId))
  showSocEditor.value = true
}

function confirmSoc(): void {
  mqttStore.setVehicleManualSoc(props.vehicleId, socInputValue.value, props.chargePointId)
  showSocEditor.value = false
}
</script>
