<script>
import { useMqttStore } from "@/stores/mqtt.js";

export default {
  name: "WelcomeView",
  data() {
    return {
      mqttStore: useMqttStore(),
    };
  },
  computed: {
    firstView() {
      if (this.mqttStore.getThemeConfiguration) {
        if (this.mqttStore.getThemeConfiguration.enable_dashboard_view) {
          return "dash-board";
        }
        if (this.mqttStore.getThemeConfiguration.enable_energy_flow_view) {
          return "energy-flow";
        }
        if (this.mqttStore.getThemeConfiguration.enable_charge_points_view) {
          return "charge-points";
        }
        if (this.mqttStore.getThemeConfiguration.enable_status_view) {
          return "status";
        }
      }
      return undefined;
    },
  },
  mounted() {
    setTimeout(this.selectFirstRoute, 3000);
  },
  methods: {
    selectFirstRoute() {
      if (this.firstView) {
        this.$router.push({ name: this.firstView });
      } else {
        console.warn("no router view enabled, check your configuration!");
      }
    },
  },
};
</script>

<template>
  <i-container>
    <i-row
      center
      middle
    >
      <i-column>
        <i-card color="primary">
          <template #header>
            Cards Theme
          </template>
          <img
            class="logo"
            src="/openWB_logo_dark.png"
          >
        </i-card>
      </i-column>
    </i-row>
  </i-container>
</template>

<style scoped>
.container,
.row {
  height: 100vh;
}

.card {
  ----background: inherit !important;
  ----body--color: var(--contrast-color-for-dark-background) !important;
}

img.logo {
  max-width: 100%;
}
</style>
