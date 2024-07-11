<script>
import { useMqttStore } from "@/stores/mqtt.js";
import DashBoardCard from "@/components/DashBoardCard.vue";
import SparkLine from "@/components/SparkLine.vue";

/* fontawesome */
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { faCarBattery as fasCarBattery } from "@fortawesome/free-solid-svg-icons";
/* add icons to the library */
library.add(fasCarBattery);

export default {
  name: "BatteryCard",
  components: { DashBoardCard, SparkLine, FontAwesomeIcon },
  props: {},
  data() {
    return {
      mqttStore: useMqttStore(),
    };
  },
};
</script>

<template>
  <dash-board-card
    v-if="mqttStore.getBatteryConfigured"
    color="warning"
  >
    <template #headerLeft>
      <font-awesome-icon
        fixed-width
        :icon="['fas', 'fa-car-battery']"
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
  </dash-board-card>
</template>
