<script>
import { useMqttStore } from "@/stores/mqtt.js";
import DashboardCard from "@/components/DashboardCard.vue";
import SparkLine from "@/components/SparkLine.vue";

/* fontawesome */
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { faHome as fasHome } from "@fortawesome/free-solid-svg-icons";
/* add icons to the library */
library.add(fasHome);

export default {
  name: "HomeCard",
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
  <dashboard-card color="light">
    <template #headerLeft>
      <font-awesome-icon
        fixed-width
        :icon="['fas', 'fa-home']"
      />
      Hausverbrauch
    </template>
    <template #headerRight>
      {{ mqttStore.getHomePower() }}
    </template>
    <spark-line
      color="var(--color--light)"
      :data="mqttStore.getHomePowerChartData"
    />
  </dashboard-card>
</template>
