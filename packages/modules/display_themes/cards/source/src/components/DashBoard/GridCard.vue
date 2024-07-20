<script>
import { useMqttStore } from "@/stores/mqtt.js";
import DashBoardCard from "@/components/DashBoardCard.vue";
import SparkLine from "@/components/SparkLine.vue";

/* fontawesome */
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { faGaugeHigh as fasGaugeHigh } from "@fortawesome/free-solid-svg-icons";
/* add icons to the library */
library.add(fasGaugeHigh);

export default {
  name: "GridCard",
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
  <dash-board-card color="danger">
    <template #headerLeft>
      <font-awesome-icon
        fixed-width
        :icon="['fas', 'fa-gauge-high']"
      />
      EVU
    </template>
    <template #headerRight>
      {{ mqttStore.getGridPower() }}
    </template>
    <spark-line
      color="var(--color--danger)"
      color-negative="var(--color--success)"
      :data="mqttStore.getGridPowerChartData"
    />
  </dash-board-card>
</template>
