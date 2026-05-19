<template>
  <q-table
    class="sticky-header-table"
    :class="{ 'custom-table-height': tableHeight }"
    :rows="mappedRows"
    :columns="mappedColumns"
    row-key="id"
    v-model:expanded="expanded"
    :filter="filterModel"
    :filter-method="customFilterMethod"
    virtual-scroll
    :virtual-scroll-item-size="48"
    :virtual-scroll-sticky-size-start="30"
    @row-click="onRowClick"
    binary-state-sort
    :pagination="{ rowsPerPage: 0 }"
    hide-bottom
    :dense="props.dense"
    :square="props.square"
  >
    <!-- search field ------------------------------------------------------->
    <template #top v-if="searchInputVisible">
      <div class="row full-width items-center">
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
    <template #body="rowProps: BodySlotProps<T>">
      <q-tr
        :key="`main-${rowProps.key}`"
        :props="rowProps"
        @click="onRowClick($event, rowProps.row)"
        class="clickable"
      >
        <q-td
          v-if="props.rowExpandable"
          auto-width
          :style="rowBorderStyle(rowProps.row)"
        >
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
        <!-- Data Columns -->
        <template v-for="(column, index) in rowProps.cols" :key="column.name">
          <q-td
            :props="{
              ...rowProps,
              col: column,
              value:
                typeof column.field === 'string'
                  ? rowProps.row[column.field]
                  : undefined,
            }"
            :class="[
              `text-${column.align || 'left'}`,
              column.shrink ? 'max-width-0' : '',
            ]"
            :auto-width="column.autoWidth"
            :style="
              index === 0 && !props.rowExpandable
                ? rowBorderStyle(rowProps.row)
                : {}
            "
          >
            <!-- Custom slot -->
            <template v-if="$slots[`body-cell-${column.name}`]">
              <slot
                :name="`body-cell-${column.name}`"
                v-bind="{ ...rowProps, col: column }"
              />
            </template>
            <!-- Default render -->
            <template v-else>
              {{
                typeof column.field === 'string'
                  ? rowProps.row[column.field]
                  : ''
              }}
            </template>
          </q-td>
        </template>
      </q-tr>
      <!-- Expansion row -->
      <q-tr
        v-if="props.rowExpandable"
        v-show="rowProps.expand"
        :key="`xp-${rowProps.key}`"
        :props="rowProps"
        class="q-virtual-scroll--with-prev"
      >
        <q-td
          :colspan="rowProps.cols.length + 1"
          :style="rowBorderStyle(rowProps.row)"
        >
          <slot name="row-expand" v-bind="rowProps" />
        </q-td>
      </q-tr>
    </template>
  </q-table>
</template>

<script setup lang="ts" generic="T extends Record<string, unknown>">
import { computed, ComputedRef, ref } from 'vue';
import type { QTableProps } from 'quasar';
import {
  ColumnConfiguration,
  BodySlotProps,
  ExtendedQTableColumn,
} from 'src/components/models/table-model';

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
  dense?: boolean;
  square?: boolean;
  rowColor?: (row: T) => string | undefined;
}>();

/* ------------------------------------------------------------------ state */
const expanded = ref<(string | number)[]>([]);
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

const mappedColumns = computed<ExtendedQTableColumn[]>(() =>
  props.columnConfig
    .filter((column) => !column.expandField) // main table columns only
    .map((column) => ({
      name: column.field,
      field: column.field,
      label: column.label,
      align: column.align ?? 'left',
      sortable: true,
      headerStyle: 'font-weight: bold',
      autoWidth: column.autoWidth,
      shrink: column.shrink ?? false,
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

const rowBorderStyle = (row: T) => {
  const color = props.rowColor?.(row);
  if (!color) return {};
  return {
    backgroundImage: `linear-gradient(${color}, ${color})`,
    backgroundRepeat: 'no-repeat',
    backgroundSize: '4px 70%',
    backgroundPosition: '4px center',
  };
};
</script>

<style scoped lang="scss">
:deep(.q-table__top) {
  padding: #{map-get($space-xs, y)} #{map-get($space-xs, x)};
}

.search-field {
  width: 100%;
  max-width: 18em;
}

.clickable {
  cursor: pointer;
}

.custom-table-height {
  height: v-bind('tableHeight');
}

.max-width-0 {
  max-width: 0;
}
</style>
