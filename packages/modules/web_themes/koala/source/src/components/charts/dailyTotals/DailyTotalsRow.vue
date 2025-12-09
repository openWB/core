<template>
  <table class="daily-table">
    <tr class="row-height">
      <td class="col-icon">
        <img :src="props.item.icon" class="icon" />
      </td>
      <td class="col-title text-weight-bold">
        <div v-if="componentNameVisible">
          <template v-if="props.item.id.startsWith('counter-')">
            <div class="ellipsis-wrapper">
              {{ props.item.title }}
              <q-tooltip>{{ props.item.title }}</q-tooltip>
            </div>
          </template>
          <template v-else>
            {{ props.item.title }}
          </template>
          <q-icon
            v-if="item.id === 'grid' && secondaryCountersConfigured"
            name="keyboard_arrow_down"
            :class="[gridExpanded ? 'rotate-180' : '', 'expand-icon']"
          />
        </div>
      </td>
      <!-- spacing added if battery SOC is visible -->
      <td :class="props.socValueVisible ? 'col-soc' : 'col-soc-spacer'">
        <span v-if="props.socValueVisible && props.item.id === 'battery'">
          {{ props.item.soc }}%
        </span>
      </td>
      <td class="col-arrow">
        <q-icon
          v-if="props.currentPowerVisible"
          :name="
            arrowDirection(props.item.id).noCurrent
              ? 'horizontal_rule'
              : 'double_arrow'
          "
          :class="{
            'rotate-180': arrowDirection(props.item.id).rotate180,
          }"
        />
      </td>
      <td class="col-power">
        <span v-if="props.currentPowerVisible">
          {{ props.item.power.replace('-', '') }}
        </span>
      </td>
      <td class="col-flex"></td>
      <td class="col-right-label text-weight-bold">
        <slot name="right-label" :item="props.item">
          <template
            v-if="
              props.item.id === 'grid' || props.item.id.startsWith('counter-')
            "
          >
            <div>Bezug:</div>
            <div>Einspeisung:</div>
          </template>
        </slot>
      </td>
      <td class="col-right-value">
        <slot name="right-value" :item="props.item">
          <template
            v-if="
              props.item.id === 'grid' || props.item.id.startsWith('counter-')
            "
          >
            <div>{{ props.item.today.imported }}</div>
            <div>{{ props.item.today.exported }}</div>
          </template>
        </slot>
      </td>
    </tr>
  </table>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import type { DailyTotalsItem } from 'src/components/models/daily-totals-model';

const mqttStore = useMqttStore();

const props = defineProps<{
  item: DailyTotalsItem;
  rowHeight: number;
  componentNameVisible: boolean;
  currentPowerVisible: boolean;
  socValueVisible: boolean;
  secondaryCountersConfigured?: boolean;
  gridExpanded?: boolean;
}>();

const rowHeightCssValue = computed(() => `${props.rowHeight}px`);

const arrowDirection = (id: string) => {
  let value = 0;
  switch (id) {
    case 'grid':
      value = mqttStore.getCounterPower('value') as number;
      break;
    case 'battery':
      value = mqttStore.batteryTotalPower('value') as number;
      break;
    case 'pv':
      value = mqttStore.getPvPower('value') as number;
      break;
    case 'house':
      value = mqttStore.getHomePower('value') as number;
      break;
    case 'chargepoint':
      value = mqttStore.chargePointSumPower('value') as number;
      break;
    default:
      if (id.startsWith('counter-')) {
        const counterId = Number(id.replace('counter-', ''));
        value = mqttStore.getCounterPower('value', counterId) as number;
      }
  }
  const noCurrent = value === 0;
  let rotate180 = false;

  if (id === 'grid' || id.startsWith('counter-')) {
    rotate180 = value < 0;
  } else if (id !== 'house') {
    rotate180 = value > 0;
  }

  return { noCurrent, rotate180 };
};
</script>

<style scoped>
.daily-table {
  width: 100%;
  min-height: 42px;
  border-collapse: collapse;
}
.daily-table td {
  padding: 0px 6px !important;
  white-space: nowrap;
  vertical-align: middle;
}
.row-height {
  height: v-bind(rowHeightCssValue);
}
.daily-table td.col-icon img {
  width: 28px;
  display: block;
  margin: 0 auto;
}
.col-icon {
  width: 32px;
}
.col-title {
  width: 85px;
  max-width: 85px;
}
.ellipsis-wrapper {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 85px;
}
.col-soc {
  width: 50px;
  text-align: right;
  white-space: nowrap;
}
.col-soc-spacer {
  width: 0 !important;
  padding: 0 !important;
  border: 0 !important;
  overflow: hidden !important;
}
.col-arrow {
  width: 24px;
  text-align: center;
}
.col-power {
  width: 70px;
  text-align: right;
  white-space: nowrap;
}
.col-flex {
  width: auto;
}
.col-right-label {
  width: 100px;
  text-align: right;
  white-space: nowrap;
}
.col-right-value {
  width: 85px;
  text-align: right;
  white-space: nowrap;
}

.icon {
  filter: brightness(0.4);
}
.rotate-180 {
  transform: rotate(180deg);
}
.expand-icon {
  font-size: 20px;
  margin-left: 8px;
  cursor: pointer;
}
@media (max-width: 500px) {
  .daily-table td {
    font-size: 13px;
  }
}
</style>
