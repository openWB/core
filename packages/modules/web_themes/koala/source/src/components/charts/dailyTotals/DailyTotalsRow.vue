<template>
  <div class="component-container">
    <!-- Icon -->
    <div class="col-icon">
      <img :src="props.item.icon" class="icon" />
    </div>
    <!-- Title -->
    <div class="col-title text-weight-bold">
      <div v-if="componentNameVisible" class="title-wrapper">
        <template v-if="props.item.id.startsWith('counter-')">
          <div class="ellipsis-wrapper">
            {{ props.item.title }}
            <q-tooltip>{{ props.item.title }}</q-tooltip>
          </div>
        </template>
        <template v-else>
          {{ props.item.title }}
        </template>
        <!-- Expansion chevron icon -->
        <q-icon
          v-if="props.item.id === 'grid' && secondaryCountersConfigured"
          name="keyboard_arrow_down"
          :class="['expand-icon', { 'rotate-180': gridExpanded }]"
        />
      </div>
    </div>
    <!-- SOC -->
    <div :class="props.socValueVisible ? 'col-soc' : 'col-soc-spacer'">
      <span v-if="props.socValueVisible && props.item.id === 'battery'">
        {{ props.item.soc }}%
      </span>
    </div>
    <!-- Arrow -->
    <div class="col-arrow">
      <q-icon
        v-if="props.currentPowerVisible"
        :name="
          arrowDirection(item.id).noCurrent ? 'horizontal_rule' : 'double_arrow'
        "
        :class="{ 'rotate-180': arrowDirection(props.item.id).rotate180 }"
      />
    </div>
    <!-- Power -->
    <div class="col-power">
      <span v-if="props.currentPowerVisible">
        {{ props.item.power.replace('-', '') }}
      </span>
    </div>

    <div class="col-flex"></div>

    <!-- Right label -->
    <div class="col-right-label text-weight-bold">
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
    </div>
    <!-- Right value -->
    <div class="col-right-value">
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
    </div>
  </div>
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

  if (id === 'grid' || id.startsWith('counter-')) rotate180 = value < 0;
  else rotate180 = value > 0;

  return { noCurrent, rotate180 };
};
</script>

<style scoped>
.component-container {
  display: flex;
  align-items: center;
  width: 100%;
  height: v-bind(rowHeightCssValue);
  gap: 0.4rem;
  font-size: 0.9rem;
  padding-inline: 0.5rem;
}
/* allow columns to shrink properly in flex layout */
.component-container > div {
  min-width: 0;
  flex-shrink: 1;
}
.col-icon {
  flex: 0 0 2rem;
  display: flex;
  justify-content: center;
}
.icon {
  width: 1.75rem;
  filter: brightness(0.4);
}
.body--dark .icon {
  filter: brightness(1);
}
.col-title {
  flex: 0 0 5.5rem;
}
.title-wrapper {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}
.ellipsis-wrapper {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.expand-icon {
  font-size: 1.3rem;
}
.rotate-180 {
  transform: rotate(180deg);
}
.col-soc {
  flex: 0 0 3rem;
  text-align: right;
  white-space: nowrap;
}
.col-soc-spacer {
  flex: 0 0 0;
  overflow: hidden;
}
.col-arrow {
  flex: 0 0 1.3rem;
  text-align: center;
}
.col-power {
  flex: 0 0 4rem;
  text-align: right;
  white-space: nowrap;
}
/* flexible column before right-side labels */
.col-flex {
  flex: 1 1 auto;
}
.col-right-label,
.col-right-value {
  display: grid;
  grid-template-rows: auto auto;
  align-items: center;
  white-space: nowrap;
}
.col-right-label {
  flex: 0 0 5rem;
  text-align: right;
}
.col-right-value {
  flex: 0 0 5rem;
  text-align: right;
}

@media (max-width: 480px) {
  .component-container {
    font-size: 0.85rem;
    gap: 0.3rem;
  }
  .col-title {
    flex: 0 0 4.2rem;
  }
  .col-soc {
    flex: 0 0 2.3rem;
  }
  .col-power {
    flex: 0 0 3.4rem;
  }
  .col-right-label {
    flex: 0 0 5rem;
  }
  .col-right-value {
    flex: 0 0 5.5rem;
  }
}

@media (max-width: 380px) {
  .component-container {
    font-size: 0.75rem;
  }
  .col-title {
    flex: 0 0 3.5rem;
  }
  .col-soc {
    flex: 0 0 1.8rem;
  }
  .col-power {
    flex: 0 0 2.8rem;
  }
  .col-right-label {
    flex: 0 0 8rem;
  }
  .col-right-value {
    flex: 0 0 5.5rem;
  }
}
</style>
