<script>
import { useMqttStore } from "@/stores/mqtt.js";
import GridCard from "@/components/Dashboard/GridCard.vue";
import BatteryCard from "@/components/Dashboard/BatteryCard.vue";
import InverterCard from "@/components/Dashboard/InverterCard.vue";
import HomeCard from "@/components/Dashboard/HomeCard.vue";
import ChargePointsCard from "@/components/Dashboard/ChargePointsCard.vue";

export default {
  name: "DashboardView",
  components: {
    GridCard,
    HomeCard,
    BatteryCard,
    InverterCard,
    ChargePointsCard,
  },
  props: {
    changesLocked: { required: false, type: Boolean, default: false },
  },
  data() {
    return {
      mqttStore: useMqttStore(),
    };
  },
};
</script>

<template>
  <div class="dashboard-card-wrapper">
    <grid-card v-if="mqttStore.getGridCardEnabled" />
    <home-card v-if="mqttStore.getHomeCardEnabled" />
    <battery-card v-if="mqttStore.getBatteryCardEnabled" />
    <inverter-card v-if="mqttStore.getPvCardEnabled" />
    <charge-points-card v-if="mqttStore.getChargePointsCardEnabled" />
  </div>
</template>

<style scoped>
.dashboard-card-wrapper {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(18rem, 1fr));
  grid-gap: var(--spacing);
}
</style>
