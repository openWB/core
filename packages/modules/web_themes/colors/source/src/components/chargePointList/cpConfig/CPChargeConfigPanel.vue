<template>
    

    <ConfigItem title="Status" icon="fa-info-circle" :fullwidth="true">
      <span class="status-string">{{ cp.stateStr }}</span>
    </ConfigItem>
  
  <ConfigItem title="Fehler" v-if="cp.faultState != 0">
    <span style="color: red"> {{ cp.faultStr }} </span>
  </ConfigItem>

  <div class="m-0 mt-4 p-0">
    
    <nav class="nav nav-tabs nav-justified mx-1 mt-1" role="tablist">
      <a
        class="nav-link active"
        data-bs-toggle="tab"
        :data-bs-target="'#chargeSettings' + cpid"
      >
        <i class="fa-solid fa-charging-station"></i>
      </a>
      <a
        class="nav-link"
        data-bs-toggle="tab"
        :data-bs-target="'#instantSettings' + cpid"
        v-if="chargepoint.chargeMode == 'instant_charging'"
      >
        <i class="fa-solid fa-lg fa-bolt"></i>
      </a>
      <a
        class="nav-link"
        data-bs-toggle="tab"
        :data-bs-target="'#pvSettings' + cpid"
        v-if="chargepoint.chargeMode == 'pv_charging'"
      >
        <i class="fa-solid fa-solar-panel me-1"></i>
      </a>
      <a
        class="nav-link"
        data-bs-toggle="tab"
        :data-bs-target="'#scheduledSettings' + cpid"
        v-if="chargepoint.chargeMode == 'scheduled_charging'"
      >
        <i class="fa-solid fa-bullseye me-1"></i>
      </a>
      <a
        class="nav-link"
        data-bs-toggle="tab"
        :data-bs-target="'#timeSettings' + cpid"
        v-if="chargepoint.scheduledCharging"
      >
        <i class="fa-solid fa-clock"></i>
      </a>
      <a
        class="nav-link"
        data-bs-toggle="tab"
        :data-bs-target="'#carSettings' + cpid"
        
      >
        <i class="fa-solid fa-rectangle-list"></i>
      </a>
    </nav>
  
    <!-- Tab panes -->
    <div class="tab-content mx-1 p-1 pb-3" id="settingsPanes">
      <div
        class="tab-pane active"
        :id="'chargeSettings' + cpid"
        role="tabpanel"
        aria-labelledby="instant-tab"
      >
        <CPChargeConfig :chargepoint="chargepoint"></CPChargeConfig>
      
      </div>
      <div
        class="tab-pane"
        :id="'instantSettings' + cpid"
        role="tabpanel"
        aria-labelledby="instant-tab"
      >
        <CPConfigInstant
          :chargepoint="cp"
          :vehicles="vehicles"
          :chargeTemplates="chargeTemplates"
        >
        </CPConfigInstant>
      </div>

      <div
        class="tab-pane"
        :id="'pvSettings' + cpid"
        role="tabpanel"
        aria-labelledby="pv-tab"
      >
        <CPConfigPv
          :chargepoint="cp"
          :vehicles="vehicles"
          :chargeTemplates="chargeTemplates"
        >
        </CPConfigPv>
      </div>
      <div
        class="tab-pane"
        :id="'scheduledSettings' + cpid"
        role="tabpanel"
        aria-labelledby="scheduled-tab"
      >
        <CPConfigScheduled
          :chargeTemplate="chargeTemplate"
          :chargeTemplateId="cp.chargeTemplate"
          v-if="chargeTemplate != undefined"
        >
        </CPConfigScheduled>
      </div>
      <div
        class="tab-pane"
        :id="'timeSettings' + cpid"
        role="tabpanel"
        aria-labelledby="time-tab"
      >
        <CPConfigTimed
          :chargeTemplate="chargeTemplate"
          :chargeTemplateId="cp.chargeTemplate"
          v-if="chargeTemplate != undefined"
        ></CPConfigTimed>
      </div>

      <div
        class="tab-pane"
        :id="'carSettings' + cpid"
        role="tabpanel"
        aria-labelledby="car-tab"
      >
        <CPConfigVehicle :vehicleId="cp.connectedVehicle"
        v-if="vehicles[cp.connectedVehicle] != undefined"
        ></CPConfigVehicle>
      </div>
    </div>
  </div>

</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { ChargePoint, vehicles, chargeTemplates } from '../model'
import ConfigItem from '../../shared/ConfigItem.vue'
import CPConfigInstant from './CPConfigInstant.vue'
import CPConfigPv from './CPConfigPv.vue'
import CPConfigScheduled from './CPConfigScheduled.vue'
import CPConfigTimed from './CPConfigTimed.vue'
import CPConfigVehicle from './CPConfigVehicle.vue'
import CPChargeConfig from './CPChargeConfig.vue'
import WbWidgetFlex from '@/components/shared/WbWidgetFlex.vue'
import WbSubwidget from '@/components/shared/WbSubwidget.vue'
const props = defineProps<{
  chargepoint: ChargePoint
}>()
const emit = defineEmits(['closeConfig'])
//state
const cp = props.chargepoint

// computed
const chargeTemplate = computed(() => {
  return chargeTemplates[cp.chargeTemplate]
})
const cpid = computed(() => {
  return cp.id
})
// methods
function closeConfig() {
  emit('closeConfig')
}
// lifecycle
onMounted(() => {})
</script>

<style scoped>
.status-string {
  font-size: var(--font-settings);
  font-style: italic;
  color: var(--color-battery);
}

.nav-tabs .nav-link {
  color: var(--color-menu);
  opacity: 0.5;
}
.nav-tabs .nav-link.disabled {
  color: var(--color-axis);
  border: 0.5px solid var(--color-axis);
}

.nav-tabs .nav-link.active {
  color: var(--color-fg);
  background-color: var(--color-bg);
  opacity: 1;
  border: 1px solid var(--color-menu);
  border-bottom: 0px solid var(--color-menu);
}
.heading {
  color: var(--color-menu);
}
</style>
