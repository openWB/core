<template>
  <div
    class="component-container"
    :class="{ 'totals-hidden': hideDailyTotals }"
  >
    <div class="component-heading">
      <!-- Icon -->
      <div class="col-icon">
        <component
          :is="iconMap[props.item.icon as keyof typeof iconMap]"
          class="base-icon"
          :style="{ color: props.item.color || 'var(--q-diagram-icon)' }"
        />
      </div>
      <!-- Title -->
      <div class="col-title text-weight-bold">
        <div v-if="componentNameVisible" class="title-wrapper">
          <template v-if="props.item.level === 'secondary'">
            <div class="ellipsis-wrapper">
              {{ props.item.title }}
              <q-tooltip>{{ props.item.title }}</q-tooltip>
            </div>
          </template>
          <template v-else>
            <div class="ellipsis-wrapper">
              {{ props.item.title }}
              <q-tooltip>{{ props.item.title }}</q-tooltip>
            </div>
          </template>
          <!-- Expansion chevron icon -->
          <q-icon
            v-if="secondaryComponentsConfigured"
            name="keyboard_arrow_down"
            :class="['expand-icon', { 'rotate-180': rowExpanded }]"
          />
        </div>
      </div>
    </div>
    <div class="component-reading">
      <!-- SOC -->
      <div :class="props.socValueVisible ? 'col-soc' : 'col-soc-spacer'">
        <span
          v-if="
            props.socValueVisible &&
            props.item.icon === 'battery' &&
            Number.isFinite(props.item.soc)
          "
        >
          {{ props.item.soc }}%
        </span>
      </div>
      <!-- Arrow -->
      <div class="col-arrow">
        <q-icon
          v-if="props.currentPowerVisible && props.item.power !== undefined"
          :name="arrowDirection.noCurrent ? 'horizontal_rule' : 'double_arrow'"
          :class="{ 'rotate-180': arrowDirection.rotate180 }"
        />
      </div>
      <!-- Power -->
      <div class="col-power">
        <span
          v-if="props.currentPowerVisible && props.item.power !== undefined"
        >
          {{ props.item.power.replace('-', '') }}
        </span>
      </div>
    </div>

    <div class="col-flex"></div>

    <!-- Right label -->
    <div v-if="!hideDailyTotals" class="col-right-label text-weight-bold">
      <slot name="right-label" :item="props.item">
        <template
          v-if="
            (props.item.id === 'grid' ||
              props.item.id.startsWith('counter-') ||
              props.item.id.startsWith('chargepoint-')) &&
            props.item.today !== undefined
          "
        >
          <div>Bezug:</div>
          <div>Einspeisung:</div>
        </template>
      </slot>
    </div>
    <!-- Right value -->
    <div v-if="!hideDailyTotals" class="col-right-value">
      <slot name="right-value" :item="props.item">
        <template
          v-if="
            (props.item.id === 'grid' ||
              props.item.id.startsWith('counter-') ||
              props.item.id.startsWith('chargepoint-')) &&
            props.item.today !== undefined
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
import type { DailyTotalsItem } from 'src/components/models/daily-totals-model';
import BatteryIcon from 'src/assets/icons/owbBattery_2.svg?component';
import GridIcon from 'src/assets/icons/owbGrid.svg?component';
import PvIcon from 'src/assets/icons/owbPV.svg?component';
import HouseIcon from 'src/assets/icons/owbHouse.svg?component';
import VehicleIcon from 'src/assets/icons/owbVehicle.svg?component';
import ChargePointIcon from 'src/assets/icons/owbChargePoint_2.svg?component';
import CounterIcon from 'src/assets/icons/owbCounter.svg?component';
import ConsumerIcon from 'src/assets/icons/owbConsumer.svg?component';

const props = defineProps<{
  item: DailyTotalsItem;
  rowHeight: number;
  componentNameVisible: boolean;
  currentPowerVisible: boolean;
  socValueVisible: boolean;
  secondaryComponentsConfigured?: boolean;
  rowExpanded?: boolean;
  hideDailyTotals?: boolean;
}>();

const rowHeightCssValue = computed(() => `${props.rowHeight}px`);

const arrowDirection = computed(() => {
  const value = props.item.powerValue ?? 0;
  const noCurrent = !Number.isFinite(value) || value === 0;
  const isCounter =
    props.item.id === 'grid' || props.item.id.startsWith('counter-');
  return {
    noCurrent,
    rotate180: !noCurrent && (isCounter ? value < 0 : value > 0),
  };
});

const iconMap = {
  grid: GridIcon,
  battery: BatteryIcon,
  chargepoint: ChargePointIcon,
  vehicle: VehicleIcon,
  pv: PvIcon,
  house: HouseIcon,
  counter: CounterIcon,
  consumer: ConsumerIcon,
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
.component-container > div,
.component-heading > div,
.component-reading > div {
  min-width: 0;
  flex-shrink: 1;
}
.component-heading,
.component-reading {
  display: contents;
}
.col-icon {
  flex: 0 0 2rem;
  display: flex;
  justify-content: center;
  align-items: center;
}
.base-icon {
  width: 1.75rem;
  height: 1.75rem;
  /* Center the visible glyph against the text, rather than its line box. */
  transform: translateY(-1px);
}
.col-title {
  flex: 0 0 5.5rem;
}
.title-wrapper {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  line-height: 1.4;
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
