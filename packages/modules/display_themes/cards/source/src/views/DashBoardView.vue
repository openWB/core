<script>
import { useMqttStore } from "@/stores/mqtt.js";
import GridCard from "@/components/DashBoard/GridCard.vue";
import BatteryCard from "@/components/DashBoard/BatteryCard.vue";
import InverterCard from "@/components/DashBoard/InverterCard.vue";
import HomeCard from "@/components/DashBoard/HomeCard.vue";
import ChargePointsCard from "@/components/DashBoard/ChargePointsCard.vue";

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
  <div class="dash-board-card-wrapper">
    <grid-card v-if="mqttStore.getGridCardEnabled" />
    <home-card v-if="mqttStore.getHomeCardEnabled" />
    <battery-card v-if="mqttStore.getBatteryCardEnabled" />
    <inverter-card v-if="mqttStore.getPvCardEnabled" />
    <charge-points-card v-if="mqttStore.getChargePointsCardEnabled" />
  </div>
</template>

<style scoped>
.dash-board-card-wrapper {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(18rem, 1fr));
  grid-gap: var(--spacing);
}
</style>
