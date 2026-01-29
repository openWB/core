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
  computed: {
    homePower() {
      return this.mqttStore.getHomePower("object");
    },
    showHomePower() {
      return this.homePower.value !== undefined;
    },
  },
};
</script>

<template>
  <dashboard-card
    v-if="showHomePower"
    color="light"
  >
    <template #headerLeft>
      <font-awesome-icon
        fixed-width
        :icon="['fas', 'fa-home']"
      />
      Hausverbrauch
    </template>
    <template #headerRight>
      {{ homePower.value.textValue }}
    </template>
    <spark-line
      color="var(--color--light)"
      :data="mqttStore.getHomePowerChartData"
    />
  </dashboard-card>
</template>
