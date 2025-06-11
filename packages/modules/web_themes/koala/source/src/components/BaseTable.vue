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
      <template v-if="props.rowExpandable" #header="header">
        <q-tr :props="header">
          <!-- space for arrow column -->
          <q-th auto-width :props="{ ...header, col: {} }" />
          <!-- the other columns -->
          <q-th
            v-for="column in header.cols"
            :key="column.name"
            :props="{ ...header, col: column }"
          >
            {{ column.label }}
          </q-th>
        </q-tr>
      </template>

      <!-- body ------------------------------------------------------------->
      <template v-if="props.rowExpandable" #body="rowProps: BodySlotProps<T>">
        <q-tr
          :key="`main-${rowProps.key}`"
          :props="rowProps"
          @click="onRowClick($event, rowProps.row)"
          class="clickable"
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

          <template v-for="column in rowProps.cols" :key="column.name">
            <!-- custom body-cell slot -->
            <template v-if="$slots[`body-cell-${column.name}`]">
              <slot
                :name="`body-cell-${column.name}`"
                v-bind="{
                  ...rowProps,
                  col: column,
                }"
              >
              </slot>
            </template>

            <!-- all other column data -->
            <q-td
              v-else
              :props="{
                ...rowProps,
                col: column,
                // cast necessary as field comes from q-table and is defined: field: string | ((row: any) => any);
                value: rowProps.row[column.field as string],
              }"
            >
              <!-- cast necessary as field comes from q-table and is defined: field: string | ((row: any) => any); -->
              {{ rowProps.row[column.field as string] }}
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
          <q-td :colspan="rowProps.cols.length + 1">
            <slot name="row-expand" v-bind="rowProps"> </slot>
          </q-td>
        </q-tr>
      </template>

      <!-- forward any other slots not related to table  e.g top search field -------------------->
      <template
        v-for="slotName in forwardedSlotNames"
        :key="slotName"
        v-slot:[slotName]="slotProps"
      >
        <slot :name="slotName" v-bind="slotProps"></slot>
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts" generic="T extends Record<string, unknown>">
import { computed, ComputedRef, ref, useSlots } from 'vue';
import type { QTableColumn, QTableProps } from 'quasar';
import { BodySlotProps } from 'src/components/models/table-model';
import { ColumnConfiguration } from 'src/components/models/table-model';

/* ------------------------------------------------------------------ props */
const props = defineProps<{
  items: number[];
  rowData: ((item: number) => T) | ComputedRef<(item: number) => T>;
  columnConfig: ColumnConfiguration[];
  rowKey?: string;
  searchInputVisible?: boolean;
  tableHeight?: string;
  filter?: string;
  columnsToSearch?: string[];
  rowExpandable?: boolean;
}>();

/* ------------------------------------------------------------------ state */
const expanded = ref<(string | number)[]>([]);
const slots = useSlots();

const forwardedSlotNames = computed(() => {
  if (props.rowExpandable)
    return Object.keys(slots).filter((name) => !name.startsWith('body'));
  return Object.keys(slots);
});

const emit = defineEmits<{
  (event: 'row-click', row: T): void;
  (event: 'update:filter', value: string): void;
}>();

/* ---------------------------------------------------------------- helpers */
const filterModel = computed({
  get: () => props.filter || '',
  set: (value) => emit('update:filter', value),
});

const mappedRows = computed(() =>
  props.items.map(
    typeof props.rowData === 'function' ? props.rowData : props.rowData.value,
  ),
);

const mappedColumns = computed<QTableColumn[]>(() =>
  props.columnConfig
    .filter((column) => !column.expandField) // main table columns only
    .map((column) => ({
      name: column.field,
      field: column.field,
      label: column.label,
      align: column.align ?? 'left',
      sortable: true,
      headerStyle: 'font-weight: bold',
    })),
);

const customFilterMethod: NonNullable<QTableProps['filterMethod']> = (
  rows,
  searchTerms,
  columns,
) => {
  if (!searchTerms || searchTerms.trim() === '') return rows;
  const lowerTerms = searchTerms.toLowerCase();
  const fields =
    props.columnsToSearch ||
    columns.map((column) =>
      typeof column.field === 'string' ? column.field : '',
    );
  return rows.filter((row) =>
    fields.some((field) => {
      const value = row[field];
      return value && String(value).toLowerCase().includes(lowerTerms);
    }),
  );
};

const onRowClick = (evt: Event, row: T) => emit('row-click', row);
</script>

<style scoped>
.search-field {
  width: 100%;
  max-width: 18em;
}

.clickable {
  cursor: pointer;
}
</style>
