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
      modalChargePointSettingsVisible: false,
    };
  },
  components: { DashBoardCard, SparkLine, FontAwesomeIcon },
  computed: {
    chargePointIds() {
      return this.mqttStore.getObjectIds("cp");
    },
    vehicleList() {
      let topicList = this.mqttStore.getWildcardTopics("openWB/vehicle/+/name");
      var vehicleList = [];
      Object.keys(topicList).forEach((topic) => {
        let id = parseInt(
          topic.match(/(?:\/)([0-9]+)(?=\/)*/g)[0].replace(/[^0-9]+/g, "")
        );
        vehicleList.push({id: id, label: topicList[topic]});
      });
      return vehicleList;
    },
  },
  methods: {
    toggleChargePointSettings(id) {
      console.log(id);
      this.modalChargePointSettingsVisible = true;
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
    getChargePointConnectedVehicle(id) {
      return {
        id: this.getChargePointConnectedVehicleId(id),
        label: this.getChargePointConnectedVehicleName(id),
      };
    },
    getChargePointConnectedVehicleId(id) {
      return this.mqttStore.topics[
        `openWB/chargepoint/${id}/get/connected_vehicle/info`
      ].id;
    },
    getChargePointConnectedVehicleName(id) {
      return this.mqttStore.topics[
        `openWB/chargepoint/${id}/get/connected_vehicle/info`
      ].name;
    },
    getChargePointConnectedVehicleSoc(id) {
      return this.mqttStore.topics[
        `openWB/chargepoint/${id}/get/connected_vehicle/soc`
      ];
    },
    setChargePointConnectedVehicle(id, $event) {
      console.log("set", id, $event);
      if ($event.id != this.getChargePointConnectedVehicleId(id)) {
        console.log("vehicle changed");
      }
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
              <i-column class="_padding-left:0 _padding-right:0">
                <i-button size="lg">
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
                </i-button>
              </i-column>
              <i-column class="_text-align:right _padding-left:0">
                {{ getChargePointPower(id) }}
                {{ getChargePointPhasesInUse(id) }}
                {{ getChargePointSetCurrent(id) }}
              </i-column>
            </i-row>
            <i-row>
              <i-column class="_padding-left:0">
                <spark-line
                  color="var(--color--primary)"
                  :data="getChargePointPowerChartData(id)"
                />
              </i-column>
            </i-row>
          </i-column>
          <i-column md="6">
            <i-row>
              <i-column class="_padding-right:0 _padding-left:0">
                <i-select
                  size="lg"
                  :model-value="getChargePointConnectedVehicle(id)"
                  :options="vehicleList"
                  placeholder="Bitte auswählen.."
                  @update:model-value="setChargePointConnectedVehicle(id, $event)"
                >
                  <template #prefix>
                    <font-awesome-icon fixed-width :icon="['fas', 'fa-car']" />
                  </template>
                  <template #suffix
                    v-if="
                      getVehicleSocConfigured(getChargePointConnectedVehicleId(id))
                    "
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
                  </template>
                </i-select>
              </i-column>
            </i-row>
            <!-- <i-row>
              <i-column>
                <spark-line
                  height="59"
                  color="var(--color--primary)"
                  :socData="getVehicleSocChartData(getChargePointConnectedVehicleId(id))"
                />
              </i-column>
            </i-row> -->
            <i-row class="_padding-top:1">
              <i-column class="_padding-left:0 _padding-right:0">
                <i-button
                  size="lg"
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
  <!-- modals -->
  <i-modal v-model="modalChargePointSettingsVisible">
    <template #header>
        Modal Header
    </template>
    This is the modal body. Useful information goes here.
    <template #footer>
        Modal Footer
    </template>
  </i-modal>
</template>

<style scoped>
.charge-points-card-wrapper {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(36rem, 1fr));
  grid-gap: var(--spacing);
}
.card {
  ----background: inherit !important;
  ----body--color: var(----color) !important;
}

:deep(.select-wrapper .input-wrapper .input-suffix > .select-caret) {
  display: none;
}
</style>
