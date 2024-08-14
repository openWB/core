<script>
import { useMqttStore } from "@/stores/mqtt.js";
import DashBoardCard from "@/components/DashBoardCard.vue";
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
    "set-charge-point-connected-vehicle-charge-mode",
  ],
  data() {
    return {
      mqttStore: useMqttStore(),
      simpleChargeModes: [
        "instant_charging",
        "pv_charging",
        "stop",
      ]
    };
  },
  computed: {
    filteredChargeModes() {
      if (this.mqttStore.getSimpleChargePointView) {
        return this.mqttStore.chargeModeList().filter((mode) => {
          return this.simpleChargeModes.includes(mode.id);
        });
      }
      return this.mqttStore.chargeModeList()
    },
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
    setChargePointConnectedVehicleChargeMode(chargePointId, modeId) {
      this.$emit("set-charge-point-connected-vehicle-charge-mode",
        chargePointId,
        modeId
      );
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
        <!-- charge point data -->
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
            <i-column class="_padding-left:0 button-group-wrapper">
              <i-button-group class="button-group main-button-group">
                <!-- Fahrzeug -->
                <i-button
                  class="large-button _flex-grow:1"
                  :class="!changesLocked ? 'clickable' : ''"
                  :disabled="changesLocked"
                  @click="handleVehicleClick(chargePointId)"
                >
                  <font-awesome-icon
                    fixed-width
                    :icon="['fas', 'fa-car']"
                  />
                  {{ mqttStore.getChargePointConnectedVehicleName(chargePointId) }}
                  <font-awesome-icon
                    class="_padding-left:1"
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
                </i-button>
                <!-- SoC -->
                <i-button
                  v-if="
                    mqttStore.getVehicleSocConfigured(
                      mqttStore.getChargePointConnectedVehicleId(chargePointId),
                    ) ||
                      mqttStore.getVehicleFaultState(
                        mqttStore.getChargePointConnectedVehicleId(chargePointId),
                      ) != 0
                  "
                  class="large-button _flex-grow:0"
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
                <!-- charge settings -->
                <i-button
                  class="large-button _flex-grow:0"
                  :class="!changesLocked ? 'clickable' : ''"
                  :disabled="changesLocked"
                  @click="toggleChargePointSettings(chargePointId)"
                >
                  <font-awesome-icon
                    fixed-width
                    :icon="['fas', 'fa-wrench']"
                  />
                </i-button>
              </i-button-group>

              <i-button-group
                class="button-group _margin-top:1"
                :disabled="changesLocked"
              >
                <!-- charge mode -->
                <i-button
                  v-for="mode in filteredChargeModes"
                  :key="mode.id"
                  outline
                  class="large-button _flex-grow:1"
                  :class="!changesLocked ? 'clickable' : ''"
                  :color="mode.class != 'dark' ? mode.class : 'light'"
                  :active="
                    mqttStore.getChargePointConnectedVehicleChargeMode(chargePointId) !=
                      undefined &&
                      mode.id ==
                      mqttStore.getChargePointConnectedVehicleChargeMode(chargePointId)
                        .mode
                  "
                  @click="
                    setChargePointConnectedVehicleChargeMode(chargePointId, mode.id)
                  "
                >
                  {{ mode.label }}
                </i-button>
              </i-button-group>
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

.large-button {
  height: 3.75rem;
  font-size: 1.5rem;
  padding: 0.75rem 1.5rem;
}

.button-group-wrapper {
  display: flex;
  flex-direction: column;
  padding-right: 0;
}

.main-button-group {
  display: flex;
  flex-wrap: wrap;
  width: 100%;
}

.button.-outline:disabled.-disabled.-active {
    ----border-color: var(----border-color--hover);
    background: var(----background);
    color: var(----color);
}
</style>
