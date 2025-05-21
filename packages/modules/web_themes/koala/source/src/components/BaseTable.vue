<template>
  <div class="q-pa-md">
    <q-table
      class="sticky-header-table"
      :rows="mappedRows"
      :columns="mappedColumns"
      row-key="id"
      v-model:expanded="expanded"
      :filter="filterModel"
      :filter-method="customFilterMethod"
      virtual-scroll
      :virtual-scroll-item-size="48"
      :virtual-scroll-sticky-size-start="48"
      :style="{ height: tableHeight }"
      @row-click="onRowClick"
      binary-state-sort
      :pagination="{ rowsPerPage: 0 }"
      hide-bottom
    >
      <!-- search field ------------------------------------------------------->
      <template #top v-if="searchInputVisible">
        <div class="row full-width items-center q-mb-sm">
          <div class="col">
            <q-input
              v-model="filterModel"
              dense
              outlined
              color="white"
              placeholder="Suchen..."
              class="search-field white-outline-input"
              input-class="text-white"
            >
              <template #append>
                <q-icon name="search" color="white" />
              </template>
            </q-input>
          </div>
        </div>
      </template>

      <!-- header ----------------------------------------------------------->
      <template v-if="props.rowExpandable" #header="hdr">
        <q-tr :props="hdr">
          <!-- space for arrow column -->
          <q-th auto-width :props="{ ...hdr, col: {} }" />

          <!-- the other columns -->
          <q-th v-for="c in hdr.cols" :key="c.name" :props="{ ...hdr, col: c }">
            {{ c.label }}
          </q-th>
        </q-tr>
      </template>

      <!-- body ------------------------------------------------------------->
      <template v-if="props.rowExpandable" #body="rowProps: BodySlotProps">
        <q-tr
          :key="`main-${rowProps.key}`"
          :props="rowProps"
          @click="onRowClick($event, rowProps.row)"
          class="mouse-over"
        >
          <q-td auto-width>
            <q-btn
              dense
              flat
              round
              size="sm"
              :icon="
                rowProps.expand ? 'keyboard_arrow_up' : 'keyboard_arrow_down'
              "
              @click.stop="rowProps.expand = !rowProps.expand"
            />
          </q-td>

          <template v-for="col in rowProps.cols" :key="col.name">
            <!-- custom body-cell slot -->
            <template v-if="$slots[`body-cell-${col.name}`]">
              <slot
                :name="`body-cell-${col.name}`"
                v-bind="{
                  ...rowProps,
                  col,
                  value: getCellValue(rowProps.row, col),
                }"
              />
            </template>

            <!-- all other column data -->
            <q-td
              v-else
              :props="{
                ...rowProps,
                col,
                value: getCellValue(rowProps.row, col),
              }"
            >
              {{ getCellValue(rowProps.row, col) }}
            </q-td>
          </template>
        </q-tr>

        <!-- expansion row -->
        <q-tr
          v-show="rowProps.expand"
          :key="`xp-${rowProps.key}`"
          :props="rowProps"
          class="q-virtual-scroll--with-prev"
        >
          <q-td colspan="100%">
            <slot name="row-expand" v-bind="rowProps">
              <pre class="text-caption q-ma-none">{{
                `row id ${rowProps.row.id}`
              }}</pre>
            </slot>
          </q-td>
        </q-tr>
      </template>

      <!-- forward any other slots not related to table  e.g top search field -------------------->
      <template
        v-for="slotName in forwardedSlotNames"
        :key="slotName"
        v-slot:[slotName]="slotProps"
      >
        <slot :name="slotName" v-bind="slotProps" />
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
import { computed, ComputedRef, ref, useSlots } from 'vue';
import type { QTableColumn, QTableProps } from 'quasar';
import { BodySlotProps } from 'src/components/Models/baseTable';

/* ------------------------------------------------------------------ props */
const props = defineProps<{
  items: number[];
  rowData:
    | ((item: number) => Record<string, unknown>)
    | ComputedRef<(item: number) => Record<string, unknown>>;
  columnConfig: {
    fields: string[];
    labels?: Record<string, string>;
    align?: Record<string, 'left' | 'right' | 'center'>;
  };
  rowKey?: string;
  searchInputVisible?: boolean;
  tableHeight?: string;
  filter?: string;
  columnsToSearch?: string[];
  rowExpandable?: boolean;
}>();

/* ------------------------------------------------------------------ utils */
function getCellValue(row: Record<string, unknown>, col: QTableColumn) {
  return typeof col.field === 'function'
    ? col.field(row)
    : row[col.field as string];
}

/* ------------------------------------------------------------------ state */
const expanded = ref<(string | number)[]>([]);
const slots = useSlots();

const forwardedSlotNames = computed(() => {
  if (props.rowExpandable)
    return Object.keys(slots).filter((n) => !n.startsWith('body'));
  return Object.keys(slots);
});

const emit = defineEmits<{
  (e: 'row-click', row: Record<string, unknown>): void;
  (e: 'update:filter', value: string): void;
}>();

/* ---------------------------------------------------------------- helpers */
const filterModel = computed({
  get: () => props.filter || '',
  set: (v) => emit('update:filter', v),
});

const rowMapperFn = computed(() =>
  typeof props.rowData === 'function' ? props.rowData : props.rowData.value,
);

const mappedRows = computed(() => props.items.map(rowMapperFn.value));

const mappedColumns = computed<QTableColumn[]>(() =>
  props.columnConfig.fields.map((field) => ({
    name: field,
    label: props.columnConfig.labels?.[field] || field,
    align: props.columnConfig.align?.[field] || 'left',
    field,
    sortable: true,
    headerStyle: 'font-weight: bold',
  })),
);

const customFilterMethod: NonNullable<QTableProps['filterMethod']> = (
  rows,
  terms,
  cols,
) => {
  if (!terms?.trim()) return rows;
  const lower = terms.toLowerCase();
  const searchFields =
    props.columnsToSearch ||
    cols.map((c) => (typeof c.field === 'string' ? c.field : ''));
  return rows.filter((r) =>
    searchFields.some((f) => {
      const val = r[f];
      return val && String(val).toLowerCase().includes(lower);
    }),
  );
};

const onRowClick = (evt: Event, row: Record<string, unknown>) =>
  emit('row-click', row);
</script>

<style scoped>
.search-field {
  width: 100%;
  max-width: 18em;
}

.mouse-over {
  cursor: pointer;
}
</style>
