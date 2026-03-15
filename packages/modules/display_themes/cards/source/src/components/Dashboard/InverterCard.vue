<script>
import { useMqttStore } from "@/stores/mqtt.js";
import DashboardCard from "@/components/DashboardCard.vue";
import SparkLine from "@/components/SparkLine.vue";

/* fontawesome */
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { faSolarPanel as fasSolarPanel } from "@fortawesome/free-solid-svg-icons";
/* add icons to the library */
library.add(fasSolarPanel);

export default {
  name: "InverterCard",
  components: { DashboardCard, SparkLine, FontAwesomeIcon },
  props: {},
  data() {
    return {
      mqttStore: useMqttStore(),
    };
  },
};
</script>

<template>
  <dashboard-card
    v-if="mqttStore.getPvConfigured"
    color="success"
  >
    <template #headerLeft>
      <font-awesome-icon
        fixed-width
        :icon="['fas', 'fa-solar-panel']"
      />
      PV
    </template>
    <template #headerRight>
      {{ mqttStore.getPvPower() }}
    </template>
    <spark-line
      color="var(--color--success)"
      :data="mqttStore.getPvPowerChartData"
      :inverted="true"
    />
  </dashboard-card>
</template>
