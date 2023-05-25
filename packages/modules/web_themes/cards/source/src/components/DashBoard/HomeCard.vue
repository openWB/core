<script>
import { useMqttStore } from "@/stores/mqtt.js";
import DashBoardCard from "@/components/DashBoardCard.vue";
import SparkLine from "@/components/SparkLine.vue";

/* fontawesome */
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { faHome as fasHome } from "@fortawesome/free-solid-svg-icons";
/* add icons to the library */
library.add(fasHome);

export default {
  name: "HomeCard",
  props: {},
  data() {
    return {
      mqttStore: useMqttStore(),
    };
  },
  components: { DashBoardCard, SparkLine, FontAwesomeIcon },
};
</script>

<template>
  <dash-board-card color="light">
    <template #headerLeft>
      <font-awesome-icon fixed-width :icon="['fas', 'fa-home']" />
      Hausverbrauch
    </template>
    <template #headerRight>
      {{ mqttStore.getHomePower }}
    </template>
    <spark-line
      color="var(--color--light)"
      :data="mqttStore.getHomePowerChartData"
    />
  </dash-board-card>
</template>
