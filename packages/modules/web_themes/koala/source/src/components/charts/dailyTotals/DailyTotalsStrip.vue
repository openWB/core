<template>
  <div class="daily-totals-strip">
    <div v-for="tile in tiles" :key="tile.item.id" class="strip-tile">
      <div
        class="tile-header"
        :class="{ 'cursor-pointer': tile.hasDetails }"
        :tabindex="tile.hasDetails ? 0 : undefined"
        :role="tile.hasDetails ? 'button' : undefined"
        :aria-expanded="tile.hasDetails ? tile.expanded : undefined"
        @click="toggle(tile)"
        @keydown.enter.prevent="toggle(tile)"
        @keydown.space.prevent="toggle(tile)"
      >
        <component
          :is="iconMap[tile.item.icon as keyof typeof iconMap]"
          class="tile-icon"
          :style="iconStyle(tile.item, 'var(--tile-icon-size)')"
        />
        <!-- Name and reading share one line while they fit, otherwise the
             reading wraps onto a second line below the name. -->
        <div class="tile-body">
          <div class="tile-name">
            <span class="tile-title text-weight-bold ellipsis">
              {{ tile.item.title }}
            </span>
            <q-icon
              v-if="tile.hasDetails"
              name="keyboard_arrow_down"
              size="xs"
              :class="{ 'rotate-180': tile.expanded }"
            />
          </div>
          <div class="tile-reading">
            <span v-if="Number.isFinite(tile.item.soc)" class="q-mr-xs">
              {{ tile.item.soc }}%
            </span>
            <template v-if="tile.item.power !== undefined">
              <q-icon
                :name="
                  powerArrow(tile.item).noCurrent
                    ? 'horizontal_rule'
                    : 'double_arrow'
                "
                :class="{ 'rotate-180': powerArrow(tile.item).rotate180 }"
              />
              <span class="text-weight-bold">
                {{ tile.item.power.replace('-', '') }}
              </span>
            </template>
          </div>
        </div>
      </div>

      <!-- Daily totals, and the individual components if there are several.
           Expands in place so the charts below move down instead of being
           covered. -->
      <q-slide-transition>
        <div v-if="tile.hasDetails && tile.expanded" class="tile-details">
          <div v-if="dailyLines(tile.item).length" class="tile-section">
            <div class="text-weight-bold">Heute</div>
            <div
              v-for="line in dailyLines(tile.item)"
              :key="line.label"
              class="tile-line"
            >
              <span>{{ line.label }}</span>
              <span>{{ line.value }}</span>
            </div>
          </div>
          <div v-for="row in tile.subItems" :key="row.id" class="tile-section">
            <div class="tile-row">
              <component
                :is="iconMap[row.icon as keyof typeof iconMap]"
                class="tile-icon"
                :style="iconStyle(row, 'var(--row-icon-size)')"
              />
              <div class="tile-body">
                <div class="tile-name">
                  <span class="tile-title ellipsis">
                    {{ row.title }}
                    <q-tooltip>{{ row.title }}</q-tooltip>
                  </span>
                </div>
                <div class="tile-reading">
                  <span v-if="Number.isFinite(row.soc)" class="q-mr-xs">
                    {{ row.soc }}%
                  </span>
                  <template v-if="row.power !== undefined">
                    <q-icon
                      :name="
                        powerArrow(row).noCurrent
                          ? 'horizontal_rule'
                          : 'double_arrow'
                      "
                      :class="{ 'rotate-180': powerArrow(row).rotate180 }"
                    />
                    <span>{{ row.power.replace('-', '') }}</span>
                  </template>
                </div>
              </div>
            </div>
            <div
              v-for="line in dailyLines(row)"
              :key="line.label"
              class="tile-line"
            >
              <span>{{ line.label }}</span>
              <span>{{ line.value }}</span>
            </div>
          </div>
        </div>
      </q-slide-transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import {
  powerArrow,
  useDailyTotalsData,
} from 'src/composables/useDailyTotalsData';
import { useLocalDataStore } from 'src/stores/localData-store';
import type { DailyTotalsItem } from 'src/components/models/daily-totals-model';
import BatteryIcon from 'src/assets/icons/owbBattery_2.svg?component';
import GridIcon from 'src/assets/icons/owbGrid.svg?component';
import PvIcon from 'src/assets/icons/owbPV.svg?component';
import HouseIcon from 'src/assets/icons/owbHouse.svg?component';
import VehicleIcon from 'src/assets/icons/owbVehicle.svg?component';
import ChargePointIcon from 'src/assets/icons/owbChargePoint_2.svg?component';
import CounterIcon from 'src/assets/icons/owbCounter.svg?component';
import ConsumerIcon from 'src/assets/icons/owbConsumer.svg?component';

defineOptions({
  name: 'DailyTotalsStrip',
});

const localDataStore = useLocalDataStore();
const {
  showGrid,
  gridData,
  secondaryCounterData,
  individualChargePointData,
  individualBatteryData,
  individualPvData,
  individualConsumerData,
  componentData,
} = useDailyTotalsData();

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

// Individual components are only listed when there is more than one,
// a single one is identical to the total shown in the tile
const subItemsFor = (id: string): DailyTotalsItem[] => {
  const lists: Record<string, DailyTotalsItem[]> = {
    grid: secondaryCounterData.value,
    chargepoint: individualChargePointData.value,
    battery: individualBatteryData.value,
    pv: individualPvData.value,
    consumer: individualConsumerData.value,
  };
  const list = lists[id] ?? [];
  if (id === 'grid') return list;
  return list.length > 1 ? list : [];
};

const tiles = computed(() => {
  const items = showGrid.value
    ? [gridData.value, ...componentData.value]
    : componentData.value;
  return items.map((item) => {
    const subItems = subItemsFor(item.id);
    return {
      item,
      subItems,
      hasDetails: dailyLines(item).length > 0 || subItems.length > 0,
      expanded: localDataStore.expandedDailyTotals.includes(item.id),
    };
  });
});

// Any number of tiles can be open at the same time
const toggle = (tile: { item: DailyTotalsItem; hasDetails: boolean }) => {
  if (!tile.hasDetails) return;
  const id = tile.item.id;
  const open = localDataStore.expandedDailyTotals;
  localDataStore.expandedDailyTotals = open.includes(id)
    ? open.filter((openId) => openId !== id)
    : [...open, id];
};

// Size is set inline: some SVG files (grid, PV) carry their own inline
// width/height, which a CSS class cannot override.
const iconStyle = (item: DailyTotalsItem, size: string) => ({
  color: item.color || 'var(--q-diagram-icon)',
  width: size,
  height: size,
});

const dailyLines = (item: DailyTotalsItem) => {
  if (item.today === undefined) return [];
  const { imported, exported } = item.today;
  switch (item.id.split('-')[0]) {
    case 'grid':
    case 'counter':
      return [
        { label: 'Bezug', value: imported },
        { label: 'Einspeisung', value: exported },
      ];
    case 'battery':
    case 'chargepoint':
      return [
        { label: 'Geladen', value: imported },
        { label: 'Entladen', value: exported },
      ];
    case 'pv':
      return [{ label: 'Ertrag', value: exported }];
    case 'house':
    case 'consumer':
      return [{ label: 'Verbrauch', value: imported }];
    default:
      return [];
  }
};
</script>

<style scoped>
.daily-totals-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(11rem, 1fr));
  /* tiles keep their own height, an open tile only grows its grid row */
  align-items: start;
  gap: var(--dashboard-gap, 0.5rem);
}

.strip-tile {
  /* icon and spacing follow the tile's own width, see @container below */
  container-type: inline-size;
  --tile-icon-size: 2.0rem;
  --row-icon-size: 1.5rem;
  min-width: 0;
  border-radius: 0.5rem;
  background: var(--q-card-background);
  filter: drop-shadow(0 0 0.15rem var(--q-chart-shadow));
  font-size: 0.9rem;
}

.tile-header,
.tile-row {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  min-width: 0;
}

.tile-header {
  gap: 0.4rem;
  padding: 0.55rem 0.75rem;
  border-radius: 0.5rem;
}

.tile-icon {
  flex: 0 0 auto;
}

/* Roboto draws digits and capitals slightly above the middle of their box,
   Material icon glyphs sit exactly in it: lift the icons to line up with the
   text. `top` instead of `transform`, which the rotated arrows already use. */
.tile-header .q-icon,
.tile-row .q-icon {
  position: relative;
  top: -0.08em;
}

.tile-title {
  min-width: 0;
}

.tile-body {
  display: flex;
  flex: 1 1 auto;
  flex-wrap: wrap;
  align-items: center;
  column-gap: 0.4rem;
  min-width: 0;
}

/* Grows on a shared line; its natural width decides when the reading wraps. */
.tile-name {
  display: flex;
  flex: 1 1 auto;
  align-items: center;
  gap: 0.3rem;
  min-width: 0;
}

.tile-reading {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  margin-left: auto;
  white-space: nowrap;
}

.tile-details {
  padding: 0 0.75rem 0.5rem;
}

.tile-section {
  border-top: 1px solid var(--q-grey-4);
  padding-top: 0.25rem;
  margin-top: 0.25rem;
}

.tile-line {
  display: flex;
  justify-content: space-between;
  line-height: 1.4rem;
  /* same size as the titles, muted to set the values apart from them */
  opacity: 0.75;
}

.rotate-180 {
  transform: rotate(180deg);
}

/* Narrow tiles, e.g. two columns on a phone. Kept last so it overrides the
   rules above. The reading always goes onto its own line so all tiles in a
   row keep the same height. */
@container (max-width: 15rem) {
  .tile-header {
    --tile-icon-size: 1.75rem;
    gap: 0.4rem;
    padding: 0.4rem 0.5rem;
    font-size: 0.8rem;
  }
  .tile-header .tile-name {
    flex-basis: 100%;
  }
  .tile-header .tile-title,
  .tile-header .tile-reading > * {
    font-weight: 500;
  }
  .tile-details {
    --row-icon-size: 1.25rem;
    padding: 0 0.5rem 0.4rem;
    font-size: 0.8rem;
  }
}
</style>
