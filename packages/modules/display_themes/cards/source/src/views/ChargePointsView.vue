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
  faStar as fasStar,
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
  fasExclamationTriangle,
  fasStar
);

export default {
  name: "ChargePointsView",
  data() {
    return {
      mqttStore: useMqttStore(),
      modalChargePointSettingsVisible: false,
    };
  },
  props: {
    changesLocked: { required: false, type: Boolean, default: false },
  },
  components: { DashBoardCard, SparkLine, FontAwesomeIcon },
  computed: {
    vehicleList() {
      let topicList = this.mqttStore.getVehicleList;
      /* topicList is an object, but we need an array for out select input */
      var vehicleList = [];
      Object.keys(topicList).forEach((topic) => {
        let id = parseInt(
          topic.match(/(?:\/)([0-9]+)(?=\/)*/g)[0].replace(/[^0-9]+/g, "")
        );
        vehicleList.push({ id: id, label: topicList[topic] });
      });
      return vehicleList;
    },
  },
  methods: {
    toggleChargePointSettings(id) {
      console.log(id);
      if (this.changesLocked) {
        console.debug("toggleChargePointSettings: changes locked!");
        return;
      }
      this.modalChargePointSettingsVisible = true;
    },
    toggleChargePointManualLock(id) {
      if (this.changesLocked) {
        console.debug("toggleChargePointManualLock: changes locked!");
        return;
      }
      this.$root.sendTopicToBroker(
        `openWB/chargepoint/${id}/set/manual_lock`,
        !this.mqttStore.getValueBool(`openWB/chargepoint/${id}/set/manual_lock`)
      );
    },
    getChargePointConnectedVehicle(id) {
      /* we need an object for our select input */
      return {
        id: this.mqttStore.getChargePointConnectedVehicleId(id),
        label: this.mqttStore.getChargePointConnectedVehicleName(id),
      };
    },
    setChargePointConnectedVehicle(id, $event) {
      console.log("set", id, $event);
      if (this.changesLocked) {
        console.debug("setChargePointConnectedVehicle: changes locked!");
        return;
      }
      if ($event.id != this.mqttStore.getChargePointConnectedVehicleId(id)) {
        console.debug("vehicle changed");
      }
    },
  },
};
</script>

<template>
  <div class="charge-points-card-wrapper">
    <dash-board-card
      v-for="id in mqttStore.getChargePointIds"
      :key="id"
      color="primary"
    >
      <template #headerLeft>
        {{ mqttStore.getChargePointName(id) }}
      </template>
      <template #headerRight>
        <i-badge size="lg">
          <font-awesome-icon
            fixed-width
            :icon="
              mqttStore.getChargePointPlugState(id)
                ? mqttStore.getChargePointChargeState(id)
                  ? ['fas', 'fa-plug-circle-bolt']
                  : ['fas', 'fa-plug-circle-check']
                : ['fas', 'fa-plug-circle-xmark']
            "
            :class="
              mqttStore.getChargePointPlugState(id)
                ? mqttStore.getChargePointChargeState(id)
                  ? ['_color:success']
                  : '_color:warning'
                : '_color:gray'
            "
          />
        </i-badge>
      </template>
      <i-container>
        <i-row>
          <!-- charge point data on left side -->
          <i-column>
            <i-row>
              <i-column class="_padding-left:0 _padding-right:0">
                <i-button
                  size="lg"
                  :disabled="changesLocked"
                  :outline="changesLocked"
                >
                  <font-awesome-icon
                    fixed-width
                    :icon="
                      mqttStore.getChargePointManualLock(id)
                        ? ['fas', 'fa-lock']
                        : ['fas', 'fa-lock-open']
                    "
                    :class="
                      mqttStore.getChargePointManualLock(id)
                        ? ['_color:danger']
                        : '_color:success'
                    "
                    @click="toggleChargePointManualLock(id)"
                  />
                </i-button>
              </i-column>
              <i-column class="_text-align:right _padding-left:0">
                {{ mqttStore.getChargePointPower(id) }}
                {{ mqttStore.getChargePointPhasesInUse(id) }}
                {{ mqttStore.getChargePointSetCurrent(id) }}
              </i-column>
            </i-row>
            <i-row>
              <i-column class="_padding-left:0">
                <spark-line
                  color="var(--color--primary)"
                  :data="mqttStore.getChargePointPowerChartData(id)"
                />
              </i-column>
            </i-row>
          </i-column>
          <!-- vehicle data on right side -->
          <i-column md="6">
            <i-row>
              <!-- vehicle select and soc -->
              <i-column class="_padding-right:0 _padding-left:0">
                <i-select
                  size="lg"
                  :disabled="changesLocked"
                  :model-value="getChargePointConnectedVehicle(id)"
                  :options="vehicleList"
                  placeholder="Bitte auswählen.."
                  @update:model-value="
                    setChargePointConnectedVehicle(id, $event)
                  "
                >
                  <template #prefix>
                    <font-awesome-icon fixed-width :icon="['fas', 'fa-car']" />
                  </template>
                  <template
                    #suffix
                    v-if="
                      mqttStore.getVehicleSocConfigured(
                        mqttStore.getChargePointConnectedVehicleId(id)
                      )
                    "
                  >
                    <font-awesome-icon
                      fixed-width
                      :icon="['fas', 'fa-car-battery']"
                    />
                    {{ mqttStore.getChargePointConnectedVehicleSoc(id).soc }}%
                    <font-awesome-icon
                      v-if="
                        mqttStore.getVehicleFaultState(
                          mqttStore.getChargePointConnectedVehicleId(id)
                        ) != 0
                      "
                      fixed-width
                      :icon="
                        mqttStore.getVehicleFaultState(
                          mqttStore.getChargePointConnectedVehicleId(id)
                        ) > 0
                          ? mqttStore.getVehicleFaultState(
                              mqttStore.getChargePointConnectedVehicleId(id)
                            ) > 1
                            ? ['fas', 'times-circle']
                            : ['fas', 'exclamation-triangle']
                          : []
                      "
                      :class="
                        mqttStore.getVehicleFaultState(
                          mqttStore.getChargePointConnectedVehicleId(id)
                        ) > 0
                          ? mqttStore.getVehicleFaultState(
                              mqttStore.getChargePointConnectedVehicleId(id)
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
            <i-row class="_padding-top:1">
              <!-- charge mode info -->
              <i-column class="_padding-right:0 _padding-left:0">
                {{ mqttStore.getChargePointConnectedVehicleChargeMode(id) }}
                <font-awesome-icon
                  v-if="mqttStore.getChargePointConnectedVehiclePriority(id)"
                  fixed-width
                  :icon="['fas', 'fa-star']"
                />
              </i-column>
            </i-row>
            <i-row v-if="!changesLocked" class="_padding-top:1">
              <i-column class="_padding-left:0 _padding-right:0">
                <i-button size="lg" @click="toggleChargePointSettings(id)">
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
    <template #header> Modal Header </template>
    This is the modal body. Useful information goes here.
    <template #footer> Modal Footer </template>
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
