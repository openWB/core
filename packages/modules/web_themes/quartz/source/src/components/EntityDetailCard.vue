<template>
  <BaseModal
    :model-value="modelValue"
    :title="title"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <div
      v-for="instance in instances"
      :key="instance.id"
      class="panel mb-3 px-4 py-3 last:mb-0"
    >
      <div class="mb-2 text-[14px] font-bold">
        {{ instance.name }}
      </div>

      <div class="settings-group-label mb-1.5">
        Aktuelle Werte
      </div>
      <div class="flex flex-wrap gap-4 text-[13px]">
        <div>
          <div class="text-muted">
            Leistung
          </div>
          <div class="font-bold">
            {{ formatKw(instance.power) }}
          </div>
        </div>
        <div
          v-for="stat in instance.stats"
          :key="stat.label"
        >
          <div class="text-muted">
            {{ stat.label }}
          </div>
          <div class="font-bold">
            {{ stat.value }}
          </div>
        </div>
      </div>

      <template v-if="instance.readings.length > 0">
        <div class="settings-group-label mt-3 mb-1.5">
          {{ instance.readingsLabel }}
        </div>
        <div class="flex flex-wrap gap-4 text-[13px]">
          <div
            v-for="reading in instance.readings"
            :key="reading.label"
          >
            <div class="text-muted">
              {{ reading.label }}
            </div>
            <div class="font-bold">
              {{ reading.value }}
            </div>
          </div>
        </div>
      </template>

      <template v-if="instance.phases.length > 0">
        <div class="settings-group-label mt-3 mb-1.5">
          Werte pro Phase
        </div>
        <table class="w-full text-[13px]">
          <tbody>
            <tr
              v-for="phase in instance.phases"
              :key="phase.label"
            >
              <td class="py-0.5 text-muted">
                {{ phase.label }}
              </td>
              <td
                v-for="(value, idx) in phase.values"
                :key="idx"
                class="py-0.5 text-right font-bold"
              >
                {{ value }}
              </td>
            </tr>
          </tbody>
        </table>
      </template>

      <div
        class="status-box mt-3"
        :class="{ 'status-box-warning': instance.faultState === 1, 'status-box-fault': instance.faultState >= 2 }"
      >
        <strong>Modulmeldung</strong>
        <p>{{ instance.faultState > 0 ? instance.faultMessage : 'Kein Fehler.' }}</p>
      </div>
    </div>
    <p
      v-if="instances.length === 0"
      class="mode-note"
    >
      Keine Daten verfügbar.
    </p>
  </BaseModal>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'
import { formatKw, formatKwh } from '@/utils/format'
import type { CategoryKey } from '@/types/chart'
import BaseModal from './BaseModal.vue'

interface InstanceInfo {
  id: number
  name: string
  power: number
  faultState: number
  faultMessage: string
  stats: { label: string; value: string }[]
  readingsLabel: string
  readings: { label: string; value: string }[]
  phases: { label: string; values: string[] }[]
}

const props = defineProps<{ modelValue: boolean; title: string; categoryKey: CategoryKey }>()
defineEmits<{ 'update:modelValue': [value: boolean] }>()

const mqttStore = useMqttStore()

function formatCurrents(values: number[]): string[] {
  return values.map((v) => v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }))
}

const instances = computed<InstanceInfo[]>(() => {
  switch (props.categoryKey) {
    case 'pv':
      return mqttStore.inverterIds.map((id) => ({
        id,
        name: mqttStore.inverterName(id),
        power: mqttStore.inverterInstancePower(id),
        faultState: mqttStore.inverterInstanceFaultState(id),
        faultMessage: mqttStore.inverterInstanceFaultMessage(id),
        stats: [{ label: 'Zählerstand', value: formatKwh(mqttStore.inverterInstanceExported(id)) }],
        readingsLabel: 'Erträge',
        readings: [
          { label: 'Heute', value: formatKwh(mqttStore.inverterInstanceDailyExported(id)) },
          { label: 'Monat', value: formatKwh(mqttStore.inverterInstanceMonthlyExported(id)) },
          { label: 'Jahr', value: formatKwh(mqttStore.inverterInstanceYearlyExported(id)) },
        ],
        phases: [{ label: 'Strom [A]', values: formatCurrents(mqttStore.inverterInstanceCurrents(id)) }],
      }))
    case 'battery':
      return mqttStore.batteryIds
        .filter((id) => id !== -1)
        .map((id) => ({
          id,
          name: mqttStore.batteryName(id),
          power: mqttStore.batteryInstancePower(id),
          faultState: mqttStore.batteryInstanceFaultState(id),
          faultMessage: mqttStore.batteryInstanceFaultMessage(id),
          stats: [{ label: 'Ladestand', value: `${Math.round(mqttStore.batteryInstanceSoc(id) ?? 0)} %` }],
          readingsLabel: 'Zählerstände',
          readings: [
            { label: 'Geladen heute', value: formatKwh(mqttStore.batteryInstanceDailyImported(id)) },
            { label: 'Geladen gesamt', value: formatKwh(mqttStore.batteryInstanceImported(id)) },
            { label: 'Entladen heute', value: formatKwh(mqttStore.batteryInstanceDailyExported(id)) },
            { label: 'Entladen gesamt', value: formatKwh(mqttStore.batteryInstanceExported(id)) },
          ],
          phases: [{ label: 'Strom [A]', values: formatCurrents(mqttStore.batteryInstanceCurrents(id)) }],
        }))
    case 'chargepoint':
      return mqttStore.chargePointIds.map((id) => ({
        id,
        name: mqttStore.chargePointName(id),
        power: mqttStore.chargePointPower(id),
        faultState: mqttStore.chargePointFaultState(id),
        faultMessage: mqttStore.chargePointFaultMessage(id),
        stats: [],
        readingsLabel: 'Zählerstände',
        readings: [{ label: 'Geladen', value: formatKwh(mqttStore.chargePointEnergyChargedPlugged(id)) }],
        phases: [],
      }))
    case 'consumer':
      return mqttStore.consumerIds.map((id) => ({
        id,
        name: mqttStore.consumerName(id),
        power: mqttStore.consumerInstancePower(id),
        faultState: mqttStore.consumerInstanceFaultState(id),
        faultMessage: mqttStore.consumerInstanceFaultMessage(id),
        stats: [],
        readingsLabel: 'Zählerstände',
        readings: [{ label: 'Verbraucht heute', value: formatKwh(mqttStore.consumerInstanceDailyImported(id)) }],
        phases: [],
      }))
    case 'grid': {
      const id = mqttStore.gridCounterId()
      if (id === undefined) return []
      return [
        {
          id,
          name: 'Netz',
          power: mqttStore.gridPower,
          faultState: mqttStore.counterInstanceFaultState(id),
          faultMessage: mqttStore.counterInstanceFaultMessage(id),
          stats: [{ label: 'Netzfrequenz', value: `${mqttStore.counterInstanceFrequency(id).toLocaleString(undefined, { maximumFractionDigits: 2 })} Hz` }],
          readingsLabel: 'Zählerstände',
          readings: [
            { label: 'Export', value: formatKwh(mqttStore.counterInstanceExported(id)) },
            { label: 'Import', value: formatKwh(mqttStore.counterInstanceImported(id)) },
          ],
          phases: [
            { label: 'Spannung [V]', values: formatCurrents(mqttStore.counterInstanceVoltages(id)) },
            { label: 'Strom [A]', values: formatCurrents(mqttStore.counterInstanceCurrents(id)) },
            { label: 'Wirkleistung [kW]', values: mqttStore.counterInstancePowers(id).map((p) => formatKw(p)) },
            { label: 'Leistungsfaktor', values: formatCurrents(mqttStore.counterInstancePowerFactors(id)) },
          ],
        },
      ]
    }
    case 'house': {
      const gridId = mqttStore.gridCounterId()
      return [
        {
          id: -1,
          name: 'Hausverbrauch',
          power: mqttStore.houseConsumption,
          faultState: gridId !== undefined ? mqttStore.counterInstanceFaultState(gridId) : 0,
          faultMessage: gridId !== undefined ? mqttStore.counterInstanceFaultMessage(gridId) : '',
          stats: [],
          readingsLabel: '',
          readings: [],
          phases: [],
        },
      ]
    }
    default:
      return []
  }
})
</script>
