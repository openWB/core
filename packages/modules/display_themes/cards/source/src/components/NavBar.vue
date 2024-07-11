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
};
</script>

<template>
  <i-nav
    vertical
    class="_align-items:stretch"
    size="lg"
  >
    <nav-item
      v-if="mqttStore.getDashBoardEnabled"
      :to="{ name: 'dash-board' }"
    >
      Übersicht
    </nav-item>
    <nav-item
      v-if="mqttStore.getEnergyFlowEnabled"
      :to="{ name: 'energy-flow' }"
    >
      Energiefluss
    </nav-item>
    <nav-item
      v-if="
        mqttStore.getChargePointsEnabled &&
          mqttStore.getChargePointIds.length > 0
      "
      :to="{ name: 'charge-points' }"
    >
      Ladepunkte
    </nav-item>
    <nav-item
      v-if="mqttStore.getStateEnabled"
      :to="{ name: 'status' }"
    >
      Status
    </nav-item>
  </i-nav>
</template>
