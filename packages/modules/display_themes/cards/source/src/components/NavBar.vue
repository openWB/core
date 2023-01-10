<script>
import { useMqttStore } from "@/stores/mqtt.js";
import NavItem from "@/components/NavItem.vue";

export default {
  name: "NavBar",
  components: { NavItem },
  data() {
    return {
      mqttStore: useMqttStore(),
    };
  },
  computed: {
    dashBoardEnabled() {
      if (this.mqttStore.getThemeConfiguration) {
        return this.mqttStore.getThemeConfiguration.enable_dashboard_view;
      }
      return true;
    },
    chargePointsEnabled() {
      if (this.mqttStore.getThemeConfiguration) {
        return this.mqttStore.getThemeConfiguration.enable_charge_points_view;
      }
      return true;
    },
    stateEnabled() {
      if (this.mqttStore.getThemeConfiguration) {
        return this.mqttStore.getThemeConfiguration.enable_status_view;
      }
      return true;
    },
  },
};
</script>

<template>
  <i-nav vertical class="_align-items:stretch">
    <nav-item v-if="dashBoardEnabled" :to="{ name: 'dash-board' }">
      DashBoard
    </nav-item>
    <nav-item v-if="chargePointsEnabled" :to="{ name: 'charge-points' }">
      Ladepunkte
    </nav-item>
    <nav-item v-if="stateEnabled" :to="{ name: 'status' }"> Status </nav-item>
  </i-nav>
</template>
