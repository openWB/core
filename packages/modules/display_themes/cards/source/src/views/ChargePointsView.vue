<script>
import { useMqttStore } from "@/stores/mqtt.js";
import DashBoardCard from "@/components/DashBoardCard.vue";
import SparkLine from "@/components/SparkLine.vue";

/* fontawesome */
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import {
  faPlugCircleXmark as fasPlugCircleXmark,
  faPlugCircleCheck as fasPlugCircleCheck,
  faPlugCircleBolt as fasPlugCircleBolt,
  faWrench as fasWrench,
} from "@fortawesome/free-solid-svg-icons";
/* add icons to the library */
library.add(
  fasPlugCircleXmark,
  fasPlugCircleCheck,
  fasPlugCircleBolt,
  fasWrench
);

export default {
  name: "ChargePoints",
  data() {
    return {
      mqttStore: useMqttStore(),
    };
  },
  components: { DashBoardCard, SparkLine, FontAwesomeIcon },
  computed: {
    chargePointIds() {
      return this.mqttStore.getObjectIds("cp");
    },
  },
  methods: {
    toggleChargePointSettings(id) {
      console.log(id);
    },
    getChargePointName(id) {
      if (
        this.mqttStore.topics[`openWB/chargepoint/${id}/config`] !== undefined
      ) {
        return this.mqttStore.topics[
          `openWB/chargepoint/${id}/config`
        ].name.toString();
      }
      return "---";
    },
    getChargePointPower(id) {
      return this.mqttStore.getValueString(
        `openWB/chargepoint/${id}/get/power`
      );
    },
    getChargePointPowerChartData(id) {
      return this.mqttStore.chartData[`openWB/chargepoint/${id}/get/power`];
    },
    getChargePointSetCurrent(id) {
      return this.mqttStore.getValueString(
        `openWB/chargepoint/${id}/set/current`,
        "A"
      );
    },
    getChargePointPhasesInUse(id) {
      const phaseSymbols = ["/", "\u2460", "\u2461", "\u2462"];
      return phaseSymbols[
        this.mqttStore.topics[`openWB/chargepoint/${id}/get/phases_in_use`]
      ];
    },
    getChargePointPlugState(id) {
      return this.mqttStore.getValueBool(
        `openWB/chargepoint/${id}/get/plug_state`
      );
    },
    getChargePointChargeState(id) {
      return this.mqttStore.getValueBool(
        `openWB/chargepoint/${id}/get/charge_state`
      );
    },
  },
};
</script>

<template>
  <div class="charge-points-card-wrapper">
    <dash-board-card v-for="id in chargePointIds" :key="id" color="primary">
      <template #headerLeft>
        {{ getChargePointName(id) }}
      </template>
      <template #headerRight>
        <i-badge size="lg">
          <font-awesome-icon
            fixed-width
            :icon="
              getChargePointPlugState(id)
                ? getChargePointChargeState(id)
                  ? ['fas', 'fa-plug-circle-bolt']
                  : ['fas', 'fa-plug-circle-check']
                : ['fas', 'fa-plug-circle-xmark']
            "
            :class="
              getChargePointPlugState(id)
                ? getChargePointChargeState(id)
                  ? ['_color:success']
                  : '_color:warning'
                : '_color_danger'
            "
          />
        </i-badge>
      </template>
      <i-container>
        <i-row>
          <i-column>
            <i-row>
              <i-column>
                {{ getChargePointPower(id) }}
                {{ getChargePointPhasesInUse(id) }}
                {{ getChargePointSetCurrent(id) }}
              </i-column>
            </i-row>
            <i-row>
              <i-column>
                <spark-line
                  color="var(--color--primary)"
                  :data="getChargePointPowerChartData(id)"
                />
              </i-column>
            </i-row>
          </i-column>
          <i-column md="6">
            <i-row>
              <i-column> Vehicle Data </i-column>
            </i-row>
            <i-row>
              <i-column>
                <i-button
                  block
                  color="dark"
                  @click="toggleChargePointSettings(id)"
                >
                  <font-awesome-icon fixed-width :icon="['fas', 'fa-wrench']" />
                </i-button>
              </i-column>
            </i-row>
          </i-column>
        </i-row>
      </i-container>
    </dash-board-card>
  </div>
</template>

<style scoped>
.charge-points-card-wrapper {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(36rem, 1fr));
  grid-gap: var(--spacing);
}
.card {
  ----background: inherit !important;
  ----body--color: var(--contrast-color-for-dark-background) !important;
}
</style>
