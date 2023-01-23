<script>
import { useMqttStore } from "@/stores/mqtt.js";
import DashBoardCard from "@/components/DashBoardCard.vue";
import SparkLine from "@/components/SparkLine.vue";

/* fontawesome */
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import {
  faChargingStation as fasChargingStation,
  faGaugeHigh as fasGaugeHigh,
  faSolarPanel as fasSolarPanel,
  faCarBattery as fasCarBattery,
  faHome as fasHome,
} from "@fortawesome/free-solid-svg-icons";
/* add icons to the library */
library.add(
  fasChargingStation,
  fasGaugeHigh,
  fasSolarPanel,
  fasCarBattery,
  fasHome
);

export default {
  name: "DashboardView",
  props: {
    changesLocked: { required: false, type: Boolean, default: false },
  },
  data() {
    return {
      mqttStore: useMqttStore(),
    };
  },
  components: { DashBoardCard, SparkLine, FontAwesomeIcon },
};
</script>

<template>
  <div class="dash-board-card-wrapper">
    <dash-board-card v-if="mqttStore.getGridCardEnabled" color="danger">
      <template #headerLeft>
        <font-awesome-icon fixed-width :icon="['fas', 'fa-gauge-high']" />
        EVU
      </template>
      <template #headerRight>
        {{ mqttStore.getGridPower }}
      </template>
      <spark-line
        color="var(--color--danger)"
        colorNegative="var(--color--success)"
        :data="mqttStore.getGridPowerChartData"
      />
    </dash-board-card>
    <dash-board-card v-if="mqttStore.getHomeCardEnabled" color="light">
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
    <dash-board-card
      color="warning"
      v-if="mqttStore.getBatteryConfigured && mqttStore.getBatteryCardEnabled"
    >
      <template #headerLeft>
        <font-awesome-icon fixed-width :icon="['fas', 'fa-car-battery']" />
        Speicher
      </template>
      <template #headerRight>
        {{ mqttStore.getBatterySoc }} /
        {{ mqttStore.getBatteryPower }}
      </template>
      <spark-line
        color="var(--color--warning)"
        :data="mqttStore.getBatteryPowerChartData"
        :socData="mqttStore.getBatterySocChartData"
      />
    </dash-board-card>
    <dash-board-card
      v-if="mqttStore.getChargePointsCardEnabled"
      color="primary"
    >
      <template #headerLeft>
        <font-awesome-icon fixed-width :icon="['fas', 'fa-charging-station']" />
        {{
          mqttStore.getChargePointIds.length == 1
            ? mqttStore.getChargePointName(mqttStore.getChargePointIds[0])
            : "Ladepunkte"
        }}
      </template>
      <template #headerRight>
        {{
          mqttStore.getChargePointIds.length == 1
            ? mqttStore.getChargePointPower(mqttStore.getChargePointIds[0])
            : mqttStore.getChargePointSumPower
        }}
      </template>
      <spark-line
        color="var(--color--primary)"
        :data="
          mqttStore.getChargePointIds.length == 1
            ? mqttStore.getChargePointPowerChartData(
                mqttStore.getChargePointIds[0]
              )
            : mqttStore.getChargePointSumPowerChartData
        "
      />
    </dash-board-card>
    <dash-board-card
      color="success"
      v-if="mqttStore.getPvConfigured && mqttStore.getPvCardEnabled"
    >
      <template #headerLeft>
        <font-awesome-icon fixed-width :icon="['fas', 'fa-solar-panel']" />
        PV
      </template>
      <template #headerRight>
        {{ mqttStore.getPvPower }}
      </template>
      <spark-line
        color="var(--color--success)"
        :data="mqttStore.getPvPowerChartData"
        :inverted="true"
      />
    </dash-board-card>
  </div>
</template>

<style scoped>
.dash-board-card-wrapper {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(18rem, 1fr));
  grid-gap: var(--spacing);
}

.card {
  ----background: inherit !important;
  ----body--color: var(--contrast-color-for-dark-background) !important;
}
</style>
