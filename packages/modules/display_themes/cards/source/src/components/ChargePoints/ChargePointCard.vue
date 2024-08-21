<script>
import { useMqttStore } from "@/stores/mqtt.js";
import DashBoardCard from "@/components/DashBoardCard.vue";
import SparkLine from "@/components/SparkLine.vue";
import ChargePointPlugBadge from "@/components/ChargePointPlugBadge.vue";
import ChargePointLockButton from "@/components/ChargePointLockButton.vue";
import ChargePointCodeButton from "@/components/ChargePointCodeButton.vue";

/* fontawesome */
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import {
  faWrench as fasWrench,
  faCar as fasCar,
  faCarBattery as fasCarBattery,
  faEdit as fasEdit,
  faTimesCircle as fasTimesCircle,
  faExclamationTriangle as fasExclamationTriangle,
  faInfoCircle as fasInfoCircle,
  faStar as fasStar,
  faClock as fasClock,
} from "@fortawesome/free-solid-svg-icons";
import {
  faStar as farStar,
  faClock as farClock,
} from "@fortawesome/free-regular-svg-icons";
/* add icons to the library */
library.add(
  fasWrench,
  fasCar,
  fasCarBattery,
  fasEdit,
  fasTimesCircle,
  fasExclamationTriangle,
  fasInfoCircle,
  fasStar,
  farStar,
  fasClock,
  farClock,
);

export default {
  name: "ChargePointCard",
  components: {
    DashBoardCard,
    SparkLine,
    ChargePointPlugBadge,
    ChargePointLockButton,
    ChargePointCodeButton,
    FontAwesomeIcon,
  },
  props: {
    chargePointId: {
      type: Number,
      required: true,
    },
    changesLocked: {
      type: Boolean,
      required: true,
    },
  },
  emits: [
    "vehicle-click",
    "soc-click",
    "charge-mode-click",
    "toggle-charge-point-settings",
  ],
  data() {
    return {
      mqttStore: useMqttStore(),
    };
  },
  methods: {
    handleVehicleClick(chargePointId) {
      this.$emit("vehicle-click", chargePointId);
    },
    handleSocClick(chargePointId) {
      this.$emit("soc-click", chargePointId);
    },
    handleChargeModeClick(chargePointId) {
      this.$emit("charge-mode-click", chargePointId);
    },
    toggleChargePointSettings(chargePointId) {
      this.$emit("toggle-charge-point-settings", chargePointId);
    },
  },
};
</script>

<template>
  <dash-board-card color="primary">
    <template #headerLeft>
      {{ mqttStore.getChargePointName(chargePointId) }}
    </template>
    <template #headerRight>
      <charge-point-plug-badge :charge-point-id="[chargePointId]" />
    </template>
    <i-container>
      <i-row>
        <!-- charge point data on left side -->
        <i-column>
          <i-row>
            <i-column class="_padding-left:0 _padding-right:0">
              <charge-point-code-button
                v-if="mqttStore.getRfidEnabled"
                :charge-point-id="chargePointId"
              />
              <charge-point-lock-button
                :charge-point-id="chargePointId"
                :changes-locked="changesLocked"
              />
            </i-column>
            <i-column class="_text-align:right _padding-left:0">
              {{ mqttStore.getChargePointPower(chargePointId) }}
              {{ mqttStore.getChargePointPhasesInUse(chargePointId) }}
              {{ mqttStore.getChargePointSetCurrent(chargePointId) }}
            </i-column>
          </i-row>
          <i-row class="_padding-top:1">
            <i-column class="_padding-left:0">
              <spark-line
                color="var(--color--primary)"
                :data="mqttStore.getChargePointPowerChartData(chargePointId)"
              />
            </i-column>
          </i-row>
        </i-column>
        <!-- vehicle data on right side -->
        <i-column md="6">
          <!-- vehicle and soc -->
          <i-row class="_display:flex">
            <i-column class="_padding-left:0 _padding-right:0 _flex-grow:1">
              <i-badge
                size="lg"
                class="_width:100%"
                :class="!changesLocked ? 'clickable' : ''"
                @click="handleVehicleClick(chargePointId)"
              >
                <font-awesome-icon
                  fixed-width
                  :icon="['fas', 'fa-car']"
                />
                {{ mqttStore.getChargePointConnectedVehicleName(chargePointId) }}
              </i-badge>
            </i-column>
            <i-column
              v-if="
                mqttStore.getVehicleSocConfigured(
                  mqttStore.getChargePointConnectedVehicleId(chargePointId),
                ) ||
                  mqttStore.getVehicleFaultState(
                    mqttStore.getChargePointConnectedVehicleId(chargePointId),
                  ) != 0
              "
              class="_flex-grow:0 _padding-right:0 _padding-left:1"
            >
              <i-button
                size="sm"
                :disabled="changesLocked"
                :class="!changesLocked ? 'clickable' : ''"
                @click="handleSocClick(chargePointId)"
              >
                <span
                  v-if="
                    mqttStore.getVehicleSocConfigured(
                      mqttStore.getChargePointConnectedVehicleId(chargePointId),
                    )
                  "
                >
                  <font-awesome-icon
                    fixed-width
                    :icon="
                      mqttStore.getVehicleSocIsManual(
                        mqttStore.getChargePointConnectedVehicleId(chargePointId),
                      )
                        ? ['fas', 'fa-edit']
                        : ['fas', 'fa-car-battery']
                    "
                  />
                  {{ mqttStore.getChargePointConnectedVehicleSoc(chargePointId).soc }}%
                </span>
                <font-awesome-icon
                  v-if="
                    mqttStore.getVehicleFaultState(
                      mqttStore.getChargePointConnectedVehicleId(chargePointId),
                    ) != 0
                  "
                  fixed-width
                  :icon="
                    mqttStore.getVehicleFaultState(
                      mqttStore.getChargePointConnectedVehicleId(chargePointId),
                    ) > 0
                      ? mqttStore.getVehicleFaultState(
                        mqttStore.getChargePointConnectedVehicleId(chargePointId),
                      ) > 1
                        ? ['fas', 'times-circle']
                        : ['fas', 'exclamation-triangle']
                      : []
                  "
                  :class="
                    mqttStore.getVehicleFaultState(
                      mqttStore.getChargePointConnectedVehicleId(chargePointId),
                    ) > 0
                      ? mqttStore.getVehicleFaultState(
                        mqttStore.getChargePointConnectedVehicleId(chargePointId),
                      ) > 1
                        ? '_color:danger'
                        : '_color:warning'
                      : ''
                  "
                />
              </i-button>
            </i-column>
          </i-row>
          <!-- charge mode info -->
          <i-row class="_padding-top:1 _display:flex">
            <i-column class="_padding-left:0 _padding-right:0 _flex-grow:1">
              <i-badge
                size="lg"
                class="_width:100%"
                :class="!changesLocked ? 'clickable' : ''"
                :color="
                  mqttStore.getChargePointConnectedVehicleChargeMode(chargePointId).class
                "
                @click="handleChargeModeClick(chargePointId)"
              >
                {{
                  mqttStore.getChargePointConnectedVehicleChargeMode(chargePointId).label
                }}
                <font-awesome-icon
                  fixed-width
                  :icon="
                    mqttStore.getChargePointConnectedVehiclePriority(chargePointId)
                      ? ['fas', 'fa-star']
                      : ['far', 'fa-star']
                  "
                  :class="
                    mqttStore.getChargePointConnectedVehiclePriority(chargePointId)
                      ? '_color:warning'
                      : ''
                  "
                />
              </i-badge>
            </i-column>
            <i-column
              v-if="
                mqttStore.getChargePointConnectedVehicleTimeChargingActive(chargePointId)
              "
              class="_flex-grow:0 _padding-right:0 _padding-left:1"
            >
              <i-badge size="lg">
                <font-awesome-icon
                  v-if="
                    mqttStore.getChargePointConnectedVehicleTimeChargingActive(
                      chargePointId,
                    )
                  "
                  fixed-width
                  :icon="
                    mqttStore.getChargePointConnectedVehicleTimeChargingRunning(
                      chargePointId,
                    )
                      ? ['fas', 'fa-clock']
                      : ['far', 'fa-clock']
                  "
                  :class="
                    mqttStore.getChargePointConnectedVehicleTimeChargingRunning(
                      chargePointId,
                    )
                      ? '_color:success'
                      : ''
                  "
                />
              </i-badge>
            </i-column>
          </i-row>
          <!-- settings button -->
          <i-row
            v-if="!changesLocked"
            class="_padding-top:1"
          >
            <i-column class="_padding-left:0 _padding-right:0">
              <i-button
                block
                @click="toggleChargePointSettings(chargePointId)"
              >
                <font-awesome-icon
                  fixed-width
                  :icon="['fas', 'fa-wrench']"
                />
              </i-button>
            </i-column>
          </i-row>
        </i-column>
      </i-row>
    </i-container>
  </dash-board-card>
</template>

<style scoped>
.card {
  ----background: inherit !important;
  ----body--color: var(----color) !important;
}

.clickable {
  cursor: pointer;
}
</style>
