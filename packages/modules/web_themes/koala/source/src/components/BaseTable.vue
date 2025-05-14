<template>
  <div class="q-pa-md">
    <q-table
      class="sticky-header-table"
      :rows="mappedRows"
      :columns="mappedColumns"
      row-key="id"
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
      <template v-slot:top v-if="searchInputVisible">
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
              <template v-slot:append>
                <q-icon name="search" color="white" />
              </template>
            </q-input>
          </div>
        </div>
      </template>

      <!-- Dynamic slot for custom cell rendering -->
      <template
        v-for="(_, name) in $slots"
        :key="name"
        v-slot:[name]="slotProps"
      >
        <!-- Add the column alignment to the slot props -->
        <slot
          :name="name"
          v-bind="{
            ...slotProps,
            columnAlignment: getColumnAlignment(
              typeof name === 'string'
                ? name.replace('body-cell-', '')
                : String(name),
            ),
          }"
        ></slot>
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
import { computed, ComputedRef } from 'vue';
import { QTableColumn, QTableProps } from 'quasar';

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
}>();

const emit = defineEmits<{
  (e: 'row-click', row: Record<string, unknown>): void;
  (e: 'update:filter', value: string): void;
}>();

const filterModel = computed({
  get: () => props.filter || '',
  set: (value) => emit('update:filter', value),
});

const getColumnAlignment = (fieldName: string): string => {
  return props.columnConfig.align?.[fieldName] || 'left';
};

// Data can be passed to basetable as a normal function or computed property
const rowMapperFn = computed(() =>
  typeof props.rowData === 'function' ? props.rowData : props.rowData.value,
);

const mappedRows = computed(() => props.items.map(rowMapperFn.value));

const mappedColumns = computed<QTableColumn[]>(() => {
  return props.columnConfig.fields.map((field) => ({
    name: field,
    label: props.columnConfig.labels?.[field] || field,
    align: props.columnConfig.align?.[field] || 'left',
    field,
    sortable: true,
    headerStyle: 'font-weight: bold',
  }));
});

const customFilterMethod: NonNullable<QTableProps['filterMethod']> = (
  rows,
  terms,
  cols,
) => {
  if (!terms || terms.trim() === '') return rows;
  const lowerTerms = terms.toLowerCase();
  const fields =
    props.columnsToSearch ||
    cols.map((col) => (typeof col.field === 'string' ? col.field : ''));
  return rows.filter((row) =>
    fields.some((field) => {
      const val = row[field];
      return val && String(val).toLowerCase().includes(lowerTerms);
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
</style>
