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
  faLock as fasLock,
  faLockOpen as fasLockOpen,
  faCar as fasCar,
  faCarBattery as fasCarBattery,
  faTimesCircle as fasTimesCircle,
  faExclamationTriangle as fasExclamationTriangle,
} from "@fortawesome/free-solid-svg-icons";
/* add icons to the library */
library.add(
  fasPlugCircleXmark,
  fasPlugCircleCheck,
  fasPlugCircleBolt,
  fasWrench,
  fasLock,
  fasLockOpen,
  fasCar,
  fasCarBattery,
  fasTimesCircle,
  fasExclamationTriangle
);

export default {
  name: "ChargePointsView",
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
    vehicleList() {
      let topicList = this.mqttStore.getWildcardTopics("openWB/vehicle/+/name");
      var vehicleList = {};
      Object.keys(topicList).forEach((topic) => {
        let id = parseInt(
          topic.match(/(?:\/)([0-9]+)(?=\/)*/g)[0].replace(/[^0-9]+/g, "")
        );
        vehicleList[id] = topicList[topic];
      });
      return vehicleList;
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
    getVehicleSocChartData(vehicleId) {
      return this.mqttStore.chartData[`openWB/vehicle/${vehicleId}/get/soc`];
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
    getChargePointManualLock(id) {
      return this.mqttStore.getValueBool(
        `openWB/chargepoint/${id}/set/manual_lock`
      );
    },
    toggleChargePointManualLock(id) {
      this.$root.sendTopicToBroker(
        `openWB/chargepoint/${id}/set/manual_lock`,
        !this.mqttStore.getValueBool(`openWB/chargepoint/${id}/set/manual_lock`)
      );
    },
    getChargePointConnectedVehicleInfo(id) {
      return this.mqttStore.topics[
        `openWB/chargepoint/${id}/get/connected_vehicle/info`
      ];
    },
    getChargePointConnectedVehicleId(id) {
      return this.mqttStore.topics[
        `openWB/chargepoint/${id}/get/connected_vehicle/info`
      ].id;
    },
    getChargePointConnectedVehicleSoc(id) {
      return this.mqttStore.topics[
        `openWB/chargepoint/${id}/get/connected_vehicle/soc`
      ];
    },
    getVehicleSocConfigured(vehicleId) {
      return (
        this.mqttStore.topics[`openWB/vehicle/${vehicleId}/soc_module/config`]
          .type != null
      );
    },
    getVehicleFaultState(vehicleId) {
      return this.mqttStore.topics[
        `openWB/vehicle/${vehicleId}/get/fault_state`
      ];
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
                : '_color:gray'
            "
          />
        </i-badge>
      </template>
      <i-container>
        <i-row>
          <i-column>
            <i-row>
              <i-column>
                <font-awesome-icon
                  fixed-width
                  :icon="
                    getChargePointManualLock(id)
                      ? ['fas', 'fa-lock']
                      : ['fas', 'fa-lock-open']
                  "
                  :class="
                    getChargePointManualLock(id)
                      ? ['_color:danger']
                      : '_color:success'
                  "
                  @click="toggleChargePointManualLock(id)"
                />
              </i-column>
              <i-column class="_text-align:right">
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
              <i-column>
                <font-awesome-icon fixed-width :icon="['fas', 'fa-car']" />
                {{ getChargePointConnectedVehicleInfo(id).name }}
              </i-column>
              <i-column
                v-if="
                  getVehicleSocConfigured(getChargePointConnectedVehicleId(id))
                "
                class="_text-align:right"
              >
                <font-awesome-icon
                  fixed-width
                  :icon="['fas', 'fa-car-battery']"
                />
                {{ getChargePointConnectedVehicleSoc(id).soc }}%
                <font-awesome-icon
                  v-if="
                    getVehicleFaultState(
                      getChargePointConnectedVehicleId(id)
                    ) != 0
                  "
                  fixed-width
                  :icon="
                    getVehicleFaultState(getChargePointConnectedVehicleId(id)) >
                    0
                      ? getVehicleFaultState(
                          getChargePointConnectedVehicleId(id)
                        ) > 1
                        ? ['fas', 'times-circle']
                        : ['fas', 'exclamation-triangle']
                      : []
                  "
                  :class="
                    getVehicleFaultState(getChargePointConnectedVehicleId(id)) >
                    0
                      ? getVehicleFaultState(
                          getChargePointConnectedVehicleId(id)
                        ) > 1
                        ? '_color:danger'
                        : '_color:warning'
                      : ''
                  "
                />
              </i-column>
            </i-row>
            <i-row>
              <i-column>
                <spark-line
                  color="var(--color--primary)"
                  :socData="getVehicleSocChartData(getChargePointConnectedVehicleId(id))"
                />
              </i-column>
            </i-row>
            <!-- <i-row>
              <i-column>
                <i-button
                  block
                  color="dark"
                  @click="toggleChargePointSettings(id)"
                >
                  <font-awesome-icon fixed-width :icon="['fas', 'fa-wrench']" />
                </i-button>
              </i-column>
            </i-row> -->
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
