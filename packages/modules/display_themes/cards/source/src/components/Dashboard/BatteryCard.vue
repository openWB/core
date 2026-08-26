<script>
import { useMqttStore } from "@/stores/mqtt.js";
import DashboardCard from "@/components/DashboardCard.vue";
import SparkLine from "@/components/SparkLine.vue";

/* fontawesome */
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { faBatteryFull as fasBatteryFull } from "@fortawesome/free-solid-svg-icons";
/* add icons to the library */
library.add(fasBatteryFull);

export default {
  name: "BatteryCard",
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
    v-if="mqttStore.getBatteryConfigured"
    color="warning"
  >
    <template #headerLeft>
      <font-awesome-icon
        fixed-width
        :icon="['fas', 'battery-full']"
        :rotation="270"
      />
      Speicher
    </template>
    <template #headerRight>
      {{ mqttStore.getBatterySoc() }} /
      {{ mqttStore.getBatteryPower() }}
    </template>
    <spark-line
      color="var(--color--warning)"
      :data="mqttStore.getBatteryPowerChartData"
      :soc-data="mqttStore.getBatterySocChartData"
    />
  </dashboard-card>
</template>
