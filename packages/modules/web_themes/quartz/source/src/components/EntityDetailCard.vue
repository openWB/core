<template>
  <BaseModal
    :model-value="modelValue"
    :title="title"
    :width="modalWidth"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <div :class="['grid gap-3', instances.length > 1 && 'sm:grid-cols-2']">
      <div
        v-for="instance in instances"
        :key="instance.id"
        class="panel px-2.5 py-2.5 sm:px-3.5 sm:py-3"
      >
        <div class="mb-2 flex items-center justify-between">
          <div class="text-[14px] font-bold">
            {{ instance.name }}
          </div>
          <div class="flex items-center gap-1.5">
            <span
              v-if="instance.meta"
              class="whitespace-nowrap rounded-full px-[9px] py-[3px] text-[11px] font-bold badge-muted"
            >{{ instance.meta }}</span>
            <span
              v-if="instance.badge"
              :class="['whitespace-nowrap rounded-full px-[9px] py-[3px] text-[11px] font-bold', `badge-${instance.badge.variant}`]"
            >{{ instance.badge.label }}</span>
          </div>
        </div>

        <DetailSection
          v-for="(section, idx) in instance.sections"
          :key="idx"
          :title="section.title"
          :tone="section.kind === 'alert' ? 'info' : 'neutral'"
        >
          <p
            v-if="section.kind === 'alert'"
            class="m-0 text-[13px] whitespace-pre-wrap"
          >
            {{ section.message }}
          </p>
          <div
            v-else-if="section.kind === 'rows'"
            class="grid grid-cols-2 gap-x-4 gap-y-2 text-[13px]"
          >
            <div
              v-for="row in section.rows"
              :key="row.label"
            >
              <div class="text-muted">
                {{ row.label }}
              </div>
              <div class="font-bold">
                {{ row.value }}
              </div>
            </div>
          </div>
          <div
            v-else-if="section.kind === 'phases'"
            class="overflow-x-auto"
          >
            <table class="w-full text-[13px]">
              <tbody>
                <tr
                  v-for="row in section.rows"
                  :key="row.label"
                >
                  <td class="py-0.5 pr-2 whitespace-nowrap text-muted">
                    {{ row.label }}
                  </td>
                  <td
                    v-for="(value, i) in row.values"
                    :key="i"
                    class="min-w-[54px] py-0.5 pl-2 text-right font-bold whitespace-nowrap"
                  >
                    {{ value }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div
            v-else
            class="overflow-x-auto"
          >
            <table class="w-full text-[13px]">
              <thead>
                <tr>
                  <th />
                  <th
                    v-for="col in section.columns"
                    :key="col"
                    class="min-w-[54px] py-0.5 pl-2 text-right text-xs font-normal whitespace-nowrap text-muted"
                  >
                    {{ col }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in section.rows"
                  :key="row.label"
                >
                  <td class="py-0.5 pr-2 whitespace-nowrap text-muted">
                    {{ row.label }}
                  </td>
                  <td
                    v-for="(value, i) in row.values"
                    :key="i"
                    class="min-w-[54px] py-0.5 pl-2 text-right font-bold whitespace-nowrap"
                  >
                    {{ value }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </DetailSection>

        <div
          v-if="categoryKey !== 'house'"
          class="status-box mt-3"
          :class="{ 'status-box-warning': instance.faultState === 1, 'status-box-fault': instance.faultState >= 2 }"
        >
          <strong>Modulmeldung</strong>
          <p>{{ instance.faultState > 0 ? instance.faultMessage : 'Kein Fehler.' }}</p>
        </div>
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
import { useCounters } from '@/composables/useCounters'
import { formatKw, formatKwh } from '@/utils/format'
import { chargeModes } from '@/utils/chargeModes'
import type { CategoryKey } from '@/types/chart'
import BaseModal from './BaseModal.vue'
import DetailSection from './DetailSection.vue'

interface RowsSection {
  kind: 'rows'
  title: string
  rows: { label: string; value: string }[]
}
interface PhasesSection {
  kind: 'phases'
  title: string
  rows: { label: string; values: string[] }[]
}
interface TableSection {
  kind: 'table'
  title: string
  columns: string[]
  rows: { label: string; values: string[] }[]
}
interface AlertSection {
  kind: 'alert'
  title: string
  message: string
}
type Section = RowsSection | PhasesSection | TableSection | AlertSection

interface InstanceInfo {
  id: number
  name: string
  badge?: { label: string; variant: 'ok' | 'wait' | 'muted' }
  // a short, static fact not worth its own boxed section (e.g. a chargepoint's max charge power)
  meta?: string
  sections: Section[]
  faultState: number
  faultMessage: string
}

const props = defineProps<{ modelValue: boolean; title: string; categoryKey: CategoryKey }>()
defineEmits<{ 'update:modelValue': [value: boolean] }>()

const mqttStore = useMqttStore()
const { counterIds } = useCounters()

function formatCurrents(values: number[]): string[] {
  return values.map((v) => v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }))
}
function formatAmp(a: number): string {
  return `${a.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} A`
}
function formatFrequency(hz: number): string {
  return `${hz.toLocaleString(undefined, { minimumFractionDigits: 3, maximumFractionDigits: 3 })} Hz`
}
// Fronius/go-eCharger-style devices sometimes report max_evse_current as a 3-phase-equivalent value even
// though the EVSE actually caps out higher on a single phase - same special case the legacy settings UI's
// own ChargePointCard.vue carries for the same reason.
function formatMaxChargePower(maxEvseCurrent: number | undefined): string {
  if (maxEvseCurrent === undefined) return '-'
  const kw = Math.floor((maxEvseCurrent * 3 * 230) / 1000)
  if (kw === 13) return '20 A 1-phasig, 16 A 3-phasig'
  return `${kw} kW`
}

function buildCounterSections(id: number): Section[] {
  return [
    {
      kind: 'rows',
      title: 'Aktuelle Werte',
      rows: [
        { label: 'Leistung', value: formatKw(mqttStore.counterInstancePower(id)) },
        { label: 'Netzfrequenz', value: formatFrequency(mqttStore.counterInstanceFrequency(id)) },
      ],
    },
    {
      kind: 'rows',
      title: 'Zählerstände',
      rows: [
        { label: 'Export', value: formatKwh(mqttStore.counterInstanceExported(id)) },
        { label: 'Import', value: formatKwh(mqttStore.counterInstanceImported(id)) },
      ],
    },
    {
      kind: 'phases',
      title: 'Werte pro Phase',
      rows: [
        { label: 'Spannung [V]', values: formatCurrents(mqttStore.counterInstanceVoltages(id)) },
        { label: 'Strom [A]', values: formatCurrents(mqttStore.counterInstanceCurrents(id)) },
        { label: 'Wirkleistung [kW]', values: formatCurrents(mqttStore.counterInstancePowers(id)) },
        { label: 'Leistungsfaktor', values: formatCurrents(mqttStore.counterInstancePowerFactors(id)) },
      ],
    },
  ]
}

const instances = computed<InstanceInfo[]>(() => {
  switch (props.categoryKey) {
    case 'pv':
      return mqttStore.inverterIds.map((id) => ({
        id,
        name: mqttStore.inverterName(id),
        sections: [
          {
            kind: 'rows',
            title: 'Aktuelle Werte',
            rows: [
              { label: 'Leistung', value: formatKw(mqttStore.inverterInstancePower(id)) },
              { label: 'Zählerstand', value: formatKwh(mqttStore.inverterInstanceExported(id)) },
            ],
          },
          {
            kind: 'rows',
            title: 'Erträge',
            rows: [
              { label: 'Heute', value: formatKwh(mqttStore.inverterInstanceDailyExported(id)) },
              { label: 'Monat', value: formatKwh(mqttStore.inverterInstanceMonthlyExported(id)) },
              { label: 'Jahr', value: formatKwh(mqttStore.inverterInstanceYearlyExported(id)) },
            ],
          },
          {
            kind: 'phases',
            title: 'Werte pro Phase',
            rows: [{ label: 'Strom [A]', values: formatCurrents(mqttStore.inverterInstanceCurrents(id)) }],
          },
        ],
        faultState: mqttStore.inverterInstanceFaultState(id),
        faultMessage: mqttStore.inverterInstanceFaultMessage(id),
      }))
    case 'battery':
      return mqttStore.batteryIds
        .map((id) => {
          const stateMessage = mqttStore.batteryInstanceStateMessage(id)
          const sections: Section[] = []
          if (stateMessage) {
            sections.push({ kind: 'alert', title: 'Status der aktiven Speichersteuerung', message: stateMessage })
          }
          sections.push(
            {
              kind: 'rows',
              title: 'Aktuelle Werte',
              rows: [
                { label: 'Leistung', value: formatKw(mqttStore.batteryInstancePower(id)) },
                { label: 'Ladestand', value: `${Math.round(mqttStore.batteryInstanceSoc(id) ?? 0)} %` },
              ],
            },
            {
              kind: 'table',
              title: 'Zählerstände',
              columns: ['Geladen', 'Entladen'],
              rows: [
                {
                  label: 'Heute',
                  values: [
                    formatKwh(mqttStore.batteryInstanceDailyImported(id)),
                    formatKwh(mqttStore.batteryInstanceDailyExported(id)),
                  ],
                },
                {
                  label: 'Gesamt',
                  values: [
                    formatKwh(mqttStore.batteryInstanceImported(id)),
                    formatKwh(mqttStore.batteryInstanceExported(id)),
                  ],
                },
              ],
            },
            {
              kind: 'phases',
              title: 'Werte pro Phase',
              rows: [{ label: 'Strom [A]', values: formatCurrents(mqttStore.batteryInstanceCurrents(id)) }],
            },
          )
          return {
            id,
            name: mqttStore.batteryName(id),
            sections,
            faultState: mqttStore.batteryInstanceFaultState(id),
            faultMessage: mqttStore.batteryInstanceFaultMessage(id),
          }
        })
    case 'chargepoint':
      return mqttStore.chargePointIds.map((id) => {
        const chargeState = mqttStore.chargePointChargeState(id)
        const plugState = mqttStore.chargePointPlugState(id)
        const badge = chargeState
          ? { label: 'Lädt', variant: 'ok' as const }
          : plugState
            ? { label: 'Angesteckt', variant: 'wait' as const }
            : { label: 'Nicht angesteckt', variant: 'muted' as const }
        const stateMessage = mqttStore.chargePointStateMessage(id)
        const sections: Section[] = []
        if (stateMessage) {
          sections.push({ kind: 'alert', title: 'Status', message: stateMessage })
        }
        sections.push(
          {
            kind: 'rows',
            title: 'Ladevorgang',
            rows: [
              { label: 'Ladestrom Vorgabe', value: formatAmp(mqttStore.chargePointChargingCurrent(id)) },
              { label: 'Leistung', value: formatKw(mqttStore.chargePointPower(id)) },
              { label: 'Phasen Vorgabe', value: `${mqttStore.chargePointPhasesToUse(id)}` },
              { label: 'Phasen Aktuell', value: `${mqttStore.chargePointPhasesInUse(id)}` },
            ],
          },
          {
            kind: 'table',
            title: 'Zählerstände',
            columns: ['Geladen', 'Entladen'],
            rows: [
              {
                label: 'Heute',
                values: [
                  formatKwh(mqttStore.chargePointInstanceDailyImported(id)),
                  formatKwh(mqttStore.chargePointInstanceDailyExported(id)),
                ],
              },
              {
                label: 'Gesamt',
                values: [
                  formatKwh(mqttStore.chargePointInstanceImported(id)),
                  formatKwh(mqttStore.chargePointInstanceExported(id)),
                ],
              },
            ],
          },
          {
            kind: 'phases',
            title: 'Werte pro Phase',
            rows: [
              { label: 'Spannung [V]', values: formatCurrents(mqttStore.chargePointInstanceVoltages(id)) },
              { label: 'Strom [A]', values: formatCurrents(mqttStore.chargePointInstanceCurrents(id)) },
              { label: 'Wirkleistung [kW]', values: formatCurrents(mqttStore.chargePointInstancePowers(id)) },
              { label: 'Leistungsfaktor', values: formatCurrents(mqttStore.chargePointInstancePowerFactors(id)) },
              { label: 'Netzfrequenz', values: [formatFrequency(mqttStore.chargePointFrequency(id))] },
            ],
          },
        )
        return {
          id,
          name: mqttStore.chargePointName(id),
          badge,
          meta: formatMaxChargePower(mqttStore.chargePointMaxEvseCurrent(id)),
          sections,
          faultState: mqttStore.chargePointFaultState(id),
          faultMessage: mqttStore.chargePointFaultMessage(id),
        }
      })
    case 'consumer':
      return mqttStore.consumerIds.map((id) => {
        const stateMessage = mqttStore.consumerInstanceStateMessage(id)
        const modeLabel = chargeModes.find((m) => m.value === mqttStore.consumerMode(id))?.label
        const temperatures = mqttStore.consumerTemperatures(id)
          .map((value, index) => ({ index, value }))
          .filter((t) => typeof t.value === 'number')
        const currents = mqttStore.consumerInstanceCurrents(id)

        const sections: Section[] = []
        if (stateMessage) {
          sections.push({ kind: 'alert', title: 'Status', message: stateMessage })
        }
        const aktuelleWerteRows = [{ label: 'Leistung', value: formatKw(mqttStore.consumerInstancePower(id)) }]
        if (modeLabel) aktuelleWerteRows.push({ label: 'Betriebsmodus', value: modeLabel })
        sections.push({ kind: 'rows', title: 'Aktuelle Werte', rows: aktuelleWerteRows })
        if (temperatures.length > 0) {
          sections.push({
            kind: 'rows',
            title: 'Temperaturen',
            rows: temperatures.map((t) => ({
              label: temperatures.length > 1 ? `Sensor ${t.index + 1}` : 'Temperatur',
              value: `${t.value.toLocaleString(undefined, { maximumFractionDigits: 1 })} °C`,
            })),
          })
        }
        if (currents.length > 0) {
          sections.push({
            kind: 'phases',
            title: 'Werte pro Phase',
            rows: [
              { label: 'Spannung [V]', values: formatCurrents(mqttStore.consumerInstanceVoltages(id)) },
              { label: 'Strom [A]', values: formatCurrents(currents) },
              { label: 'Wirkleistung [kW]', values: formatCurrents(mqttStore.consumerInstancePowers(id)) },
            ],
          })
        }
        return {
          id,
          name: mqttStore.consumerName(id),
          sections,
          faultState: mqttStore.consumerInstanceFaultState(id),
          faultMessage: mqttStore.consumerInstanceFaultMessage(id),
        }
      })
    case 'grid': {
      const id = mqttStore.gridCounterId()
      if (id === undefined) return []
      return [
        {
          id,
          name: 'Netz',
          sections: buildCounterSections(id),
          faultState: mqttStore.counterInstanceFaultState(id),
          faultMessage: mqttStore.counterInstanceFaultMessage(id),
        },
      ]
    }
    case 'house':
      // reine Rechengröße (PV + Netzbezug - Einspeisung), kein eigenes Modul -> kein Fehlerstatus
      return [
        {
          id: -1,
          name: 'Hausverbrauch',
          sections: [
            { kind: 'rows', title: 'Aktuelle Werte', rows: [{ label: 'Leistung', value: formatKw(mqttStore.houseConsumption) }] },
          ],
          faultState: 0,
          faultMessage: '',
        },
      ]
    case 'counter':
      return counterIds.value.map((id) => ({
        id,
        name: mqttStore.counterName(id),
        sections: buildCounterSections(id),
        faultState: mqttStore.counterInstanceFaultState(id),
        faultMessage: mqttStore.counterInstanceFaultMessage(id),
      }))
    default:
      return []
  }
})

// one instance doesn't need the 2-up grid's full width - narrower reads better than a half-empty row
const modalWidth = computed(() => (instances.value.length > 1 ? 880 : 480))
</script>
