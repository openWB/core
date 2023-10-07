<template>
  <WBWidget>
    <template v-slot:title> Ladepunkte </template>
    <table class="table table-borderless px-0">
      <thead>
        <tr>
          <th class="tableheader alignleft"><i class="fa-solid fa-lg fa-charging-station ps-2"></i></th>
          <th class="tableheader alignleft"><i class="fa-solid fa-lg fa-car ps-2"></i></th>
          <th class="tableheader alignleft"><i class="fa-solid fa-lg fa-bolt ps-2"></i></th>
          <th class="tableheader alignleft"><i class="fa-solid fa-lg fa-car-battery ps-2"></i></th>
          <th class="tableheader alignright"></th>
        </tr>
      </thead>
      <tbody>
        <CPSListItem
          :chargepoint="chargepoint"
          v-for="chargepoint in chargepointsToDisplay"
        ></CPSListItem>
      </tbody>
    </table>
    <ModalComponent v-for="chargepoint in chargepointsToDisplay"
      :modal-id="'cpsconfig-' + chargepoint.id">
      <template v-slot:title>Konfiguration: {{ chargepoint.name }} </template>
      <CPChargeConfigPanel
        :chargepoint="chargepoint"
        v-if="chargepoint != undefined"
      ></CPChargeConfigPanel>
    </ModalComponent>
  </WBWidget>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { chargePoints } from '../model'
import WBWidget from '@/components/shared/WBWidget.vue'
import CPSListItem from './CPSListItem.vue'
import ModalComponent from '@/components/shared/ModalComponent.vue'
import CPChargeConfigPanel from '../cpConfig/CPChargeConfigPanel.vue'
const chargepointsToDisplay = computed(() => {
  return Object.values(chargePoints)
})
</script>

<style scoped>
.tableheader {
  margin: 0;
  padding-left: 0;
  background-color: var(--color-bg);
  color: var(--color-menu);
}
.alignleft {
  text-align: left;
}
.aligncenter {
  text-align: center;
}
.alignright {
  text-align: right;
}
.table {
  border-spacing: 1rem;
  background-color: var(--color-bg);
}
</style>
