<template>
  <div class="q-pa-md">
    <q-table
      class="sticky-header-table"
      :rows="rows"
      :columns="columns"
      row-key="id"
      :filter="filter"
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
        v-slot:[name]="slotData"
      >
        <slot :name="name" v-bind="slotData"></slot>
      </template>
    </q-table>
  </div>
</template>

<style scoped>
.search-field {
  width: 100%;
  max-width: 18em;
}
</style>

<script setup lang="ts">
import { computed } from 'vue';
import { QTableColumn, QTableProps } from 'quasar';
import { BaseRow } from 'src/components/models/base-table-models';

type FilterFunction = NonNullable<QTableProps['filterMethod']>;

const props = defineProps<{
  rows: BaseRow[];
  columns: QTableColumn[];
  searchInputVisible?: boolean;
  tableHeight?: string;
  filter?: string;
  columnsToSearch?: string[];
}>();

const emit = defineEmits<{
  (e: 'row-click', row: BaseRow): void;
  (e: 'update:filter', value: string): void;
}>();

const filterModel = computed({
  get: () => props.filter || '',
  set: (value) => {
    emit('update:filter', value);
  },
});

const customFilterMethod: FilterFunction = (rows, terms, cols) => {
  if (!terms || terms.trim() === '') {
    return rows;
  }
  const lowerTerms = terms.toLowerCase();
  const columnsToSearch = props.columnsToSearch ||
    cols.map(col => typeof col.field === 'string' ? col.field : '');
  return rows.filter(row => {
    return columnsToSearch.some(field => {
      const val = row[field as keyof typeof row];
      return val !== null &&
             val !== undefined &&
             String(val).toLowerCase().includes(lowerTerms);
    });
  });
};

const onRowClick = (evt: Event, row: BaseRow) => {
  emit('row-click', row);
};
</script>
