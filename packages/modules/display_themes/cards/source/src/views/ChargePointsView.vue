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
  faClock as fasClock,
} from "@fortawesome/free-solid-svg-icons";
import {
  faStar as farStar,
  faClock as farClock,
} from "@fortawesome/free-regular-svg-icons";
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
  fasStar,
  farStar,
  fasClock,
  farClock
);

export default {
  name: "ChargePointsView",
  data() {
    return {
      mqttStore: useMqttStore(),
      modalChargePointSettingsVisible: false,
      modalChargePointSettingsId: 0,
      modalActiveTab: "tab-general",
    };
  },
  props: {
    changesLocked: { required: false, type: Boolean, default: false },
  },
  components: { DashBoardCard, SparkLine, FontAwesomeIcon },
  computed: {
    vehicleList() {
      let topicList = this.mqttStore.getVehicleList;
      /* topicList is an object, but we need an array for our select input */
      var vehicleList = [];
      Object.keys(topicList).forEach((topic) => {
        let id = parseInt(
          topic.match(/(?:\/)([0-9]+)(?=\/)*/g)[0].replace(/[^0-9]+/g, "")
        );
        vehicleList.push({ id: id, name: topicList[topic] });
      });
      return vehicleList;
    },
  },
  methods: {
    toggleChargePointSettings(id) {
      // reset selected tab if selecting different charge point
      if (this.modalChargePointSettingsId != id){
        this.modalActiveTab = "tab-general";
      }
      this.modalChargePointSettingsId = id;
      this.modalChargePointSettingsVisible = true;
    },
    toggleChargePointManualLock(id) {
      this.$root.sendTopicToBroker(
        `openWB/chargepoint/${id}/set/manual_lock`,
        !this.mqttStore.getValueBool(`openWB/chargepoint/${id}/set/manual_lock`)
      );
    },
    setChargePointConnectedVehicle(id, event) {
      if (event.id != this.mqttStore.getChargePointConnectedVehicleId(id)) {
        this.$root.sendTopicToBroker(
          `openWB/chargepoint/${id}/config/ev`,
          event.id
        );
      }
    },
    setChargePointConnectedVehicleChargeMode(id, event) {
      if (
        event.id != this.mqttStore.getChargePointConnectedVehicleChargeMode(id)
      ) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/selected`,
          event
        );
      }
    },
    setChargePointConnectedVehiclePriority(id, event) {
      if (
        event != this.mqttStore.getChargePointConnectedVehiclePriority(id)
      ) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/prio`,
          event
        );
      }
    },
    setChargePointConnectedVehicleTimeChargingActive(id, event) {
      if (
        event !=
        this.mqttStore.getChargePointConnectedVehicleTimeChargingActive(id)
      ) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/time_charging/active`,
          event
        );
      }
    },
    setChargePointConnectedVehicleInstantChargingCurrent(id, event) {
      if (
        event &&
        event !=
          this.mqttStore.getChargePointConnectedVehicleInstantChargingCurrent(
            id
          )
      ) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/instant_charging/current`,
          parseFloat(event)
        );
      }
    },
    setChargePointConnectedVehicleInstantChargingLimit(id, selected_limit) {
      if (
        selected_limit &&
        selected_limit !=
          this.mqttStore.getChargePointConnectedVehicleInstantChargingLimit(id)
            .selected
      ) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/instant_charging/limit/selected`,
          selected_limit
        );
      }
    },
    setChargePointConnectedVehicleInstantChargingLimitSoc(id, soc_limit) {
      if (
        soc_limit &&
        soc_limit !=
          this.mqttStore.getChargePointConnectedVehicleInstantChargingLimit(id)
            .soc
      ) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/instant_charging/limit/soc`,
          parseInt(soc_limit)
        );
      }
    },
    setChargePointConnectedVehicleInstantChargingLimitAmount(id, amount_limit) {
      if (
        amount_limit &&
        amount_limit !=
          this.mqttStore.getChargePointConnectedVehicleInstantChargingLimit(id)
            .amount
      ) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/instant_charging/limit/amount`,
          amount_limit
        );
      }
    },
    setChargePointConnectedVehiclePvChargingFeedInLimit(id, event) {
      if (
        event != this.mqttStore.getChargePointConnectedVehiclePvChargingFeedInLimit(id)
      ) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/pv_charging/feed_in_limit`,
          event
        );
      }
    },
    setChargePointConnectedVehiclePvChargingMinCurrent(id, event) {
      let previous_value = this.mqttStore.getChargePointConnectedVehiclePvChargingMinCurrent(id);
      let new_value = parseInt(event);
      if (new_value != previous_value && ! isNaN(new_value)) {
        // check value: 0, 6..32
        if (previous_value == 0 && new_value > 0) {
          new_value = Math.max(new_value, 6);
        }
        if (previous_value != 0 && new_value < 6) {
          new_value = 0;
        }
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/pv_charging/min_current`,
          new_value
        );
      }
    },
    setChargePointConnectedVehiclePvChargingMinSoc(id, soc) {
      let new_value = parseInt(soc);
      if (
        new_value !=
          this.mqttStore.getChargePointConnectedVehiclePvChargingMinSoc(id)
      ) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/pv_charging/min_soc`,
          new_value
        );
      }
    },
    setChargePointConnectedVehiclePvChargingMinSocCurrent(id, event) {
      let previous_value = this.mqttStore.getChargePointConnectedVehiclePvChargingMinSocCurrent(id);
      let new_value = parseInt(event);
      if (new_value != previous_value) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/pv_charging/min_soc_current`,
          new_value
        );
      }
    },
    setChargePointConnectedVehiclePvChargingMaxSoc(id, soc) {
      let new_value = parseInt(soc);
      if (
        new_value !=
          this.mqttStore.getChargePointConnectedVehiclePvChargingMaxSoc(id)
      ) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/pv_charging/max_soc`,
          new_value
        );
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
            <!-- vehicle and soc -->
            <i-row class="_display:flex">
              <i-column class="_padding-left:0 _padding-right:0 _flex-grow:1">
                <i-badge size="lg" class="full-width">
                  <font-awesome-icon fixed-width :icon="['fas', 'fa-car']" />
                  {{ mqttStore.getChargePointConnectedVehicleName(id) }}
                </i-badge>
              </i-column>
              <i-column
                v-if="
                  mqttStore.getVehicleSocConfigured(
                    mqttStore.getChargePointConnectedVehicleId(id)
                  ) ||
                  mqttStore.getVehicleFaultState(
                    mqttStore.getChargePointConnectedVehicleId(id)
                  ) != 0
                "
                class="_flex-grow:0 _padding-right:0 _padding-left:1"
              >
                <i-badge size="lg">
                  <span
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
                  </span>
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
                </i-badge>
              </i-column>
            </i-row>
            <!-- charge mode info -->
            <i-row class="_padding-top:1 _display:flex">
              <i-column class="_padding-left:0 _padding-right:0 _flex-grow:1">
                <i-badge
                  size="lg"
                  class="full-width"
                  :color="
                    mqttStore.getChargePointConnectedVehicleChargeMode(id).class
                  "
                >
                  {{
                    mqttStore.getChargePointConnectedVehicleChargeMode(id).label
                  }}
                </i-badge>
              </i-column>
              <i-column
                v-if="
                  mqttStore.getChargePointConnectedVehiclePriority(id) ||
                  mqttStore.getChargePointConnectedVehicleTimeChargingActive(id)
                "
                class="_flex-grow:0 _padding-right:0 _padding-left:1"
              >
                <i-badge size="lg">
                  <font-awesome-icon
                    v-if="mqttStore.getChargePointConnectedVehiclePriority(id)"
                    fixed-width
                    :icon="['fas', 'fa-star']"
                    class="_color:warning"
                  />
                  <font-awesome-icon
                    v-if="
                      mqttStore.getChargePointConnectedVehicleTimeChargingActive(
                        id
                      )
                    "
                    fixed-width
                    :icon="
                      mqttStore.getChargePointConnectedVehicleTimeChargingRunning(
                        id
                      )
                        ? ['fas', 'fa-clock']
                        : ['far', 'fa-clock']
                    "
                    :class="
                      mqttStore.getChargePointConnectedVehicleTimeChargingRunning(
                        id
                      )
                        ? '_color:success'
                        : ''
                    "
                  />
                </i-badge>
              </i-column>
            </i-row>
            <!-- settings button -->
            <i-row v-if="!changesLocked" class="_padding-top:1">
              <i-column class="_padding-left:0 _padding-right:0">
                <i-button block @click="toggleChargePointSettings(id)">
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
      Einstellungen für Ladepunkt "{{
        mqttStore.getChargePointName(modalChargePointSettingsId)
      }}"
    </template>
    <i-tabs v-model="modalActiveTab" stretch>
      <template #header>
        <i-tab-title for="tab-general"> Allgemein </i-tab-title>
        <i-tab-title for="tab-instant-charging"> Sofort </i-tab-title>
        <i-tab-title for="tab-pv-charging"> PV </i-tab-title>
        <i-tab-title for="tab-scheduled-charging"> Zielladen </i-tab-title>
        <i-tab-title for="tab-time-charging"> Zeitladen </i-tab-title>
      </template>

      <i-tab name="tab-general">
        <i-form>
          <i-form-group>
            <i-form-label>
              <font-awesome-icon fixed-width :icon="['fas', 'fa-car']" />
              Fahrzeug
            </i-form-label>
            <i-select
              size="lg"
              :disabled="
                !mqttStore.getChargePointVehicleChangePermitted(
                  modalChargePointSettingsId
                )
              "
              :model-value="
                mqttStore.getChargePointConnectedVehicleInfo(modalChargePointSettingsId)
              "
              label="name"
              :options="vehicleList"
              placeholder="Bitte auswählen.."
              @update:model-value="
                setChargePointConnectedVehicle(
                  modalChargePointSettingsId,
                  $event
                )
              "
            />
          </i-form-group>
          <i-form-group>
            <i-form-label>Lademodus</i-form-label>
            <i-select
              size="lg"
              :model-value="
                mqttStore.getChargePointConnectedVehicleChargeMode(
                  modalChargePointSettingsId
                )
              "
              placeholder="Bitte auswählen.."
              @update:model-value="
                setChargePointConnectedVehicleChargeMode(
                  modalChargePointSettingsId,
                  $event
                )
              "
            >
              <i-select-option
                v-for="option in mqttStore.chargeModeList()"
                :key="option.id"
                :value="option.id"
                :label="option.label"
                :class="'_background:' + option.class"
              />
            </i-select>
          </i-form-group>
          <i-form-group inline class="_justify-content:space-around">
            <i-form-group inline>
              <i-form-label placement="left" class="_align-items:center">
                <font-awesome-icon fixed-width :icon="['far', 'fa-star']" />
                Priorität
              </i-form-label>
              <i-toggle
                size="lg"
                :model-value="
                  mqttStore.getChargePointConnectedVehiclePriority(
                    modalChargePointSettingsId
                  )
                "
                @update:model-value="
                  setChargePointConnectedVehiclePriority(
                    modalChargePointSettingsId,
                    $event
                  )
                "
              />
            </i-form-group>
            <i-form-group inline class="_margin-top:0">
              <i-form-label placement="left" class="_align-items:center">
                <font-awesome-icon fixed-width :icon="['far', 'fa-clock']" />
                Zeitladen
              </i-form-label>
              <i-toggle
                size="lg"
                :model-value="
                  mqttStore.getChargePointConnectedVehicleTimeChargingActive(
                    modalChargePointSettingsId
                  )
                "
                @update:model-value="
                  setChargePointConnectedVehicleTimeChargingActive(
                    modalChargePointSettingsId,
                    $event
                  )
                "
              />
            </i-form-group>
          </i-form-group>
        </i-form>
      </i-tab>
      <i-tab name="tab-instant-charging">
        <i-form>
          <i-form-group>
            <i-form-label>Stromstärke</i-form-label>
            <i-number-input
              size="lg"
              class="_text-align:right"
              id="instant-charging-current"
              :min="6"
              :max="32"
              :model-value="
                mqttStore.getChargePointConnectedVehicleInstantChargingCurrent(
                  modalChargePointSettingsId
                )
              "
              @update:model-value="
                setChargePointConnectedVehicleInstantChargingCurrent(
                  modalChargePointSettingsId,
                  $event
                )
              "
            >
              <template #suffix>A</template>
            </i-number-input>
          </i-form-group>
          <i-form-group>
            <i-form-label>Begrenzung</i-form-label>
            <i-button-group block>
              <i-button
                :color="
                  mqttStore.getChargePointConnectedVehicleInstantChargingLimit(
                    modalChargePointSettingsId
                  ).selected == 'none'
                    ? 'primary'
                    : ''
                "
                :active="
                  mqttStore.getChargePointConnectedVehicleInstantChargingLimit(
                    modalChargePointSettingsId
                  ).selected == 'none'
                "
                @click="
                  setChargePointConnectedVehicleInstantChargingLimit(
                    modalChargePointSettingsId,
                    'none'
                  )
                "
              >
                Keine
              </i-button>
              <i-button
                :color="
                  mqttStore.getChargePointConnectedVehicleInstantChargingLimit(
                    modalChargePointSettingsId
                  ).selected == 'soc'
                    ? 'primary'
                    : ''
                "
                :active="
                  mqttStore.getChargePointConnectedVehicleInstantChargingLimit(
                    modalChargePointSettingsId
                  ).selected == 'soc'
                "
                @click="
                  setChargePointConnectedVehicleInstantChargingLimit(
                    modalChargePointSettingsId,
                    'soc'
                  )
                "
              >
                EV-SoC
              </i-button>
              <i-button
                :color="
                  mqttStore.getChargePointConnectedVehicleInstantChargingLimit(
                    modalChargePointSettingsId
                  ).selected == 'amount'
                    ? 'primary'
                    : ''
                "
                :active="
                  mqttStore.getChargePointConnectedVehicleInstantChargingLimit(
                    modalChargePointSettingsId
                  ).selected == 'amount'
                "
                @click="
                  setChargePointConnectedVehicleInstantChargingLimit(
                    modalChargePointSettingsId,
                    'amount'
                  )
                "
              >
                Energie
              </i-button>
            </i-button-group>
          </i-form-group>
          <i-form-group
            v-if="
              mqttStore.getChargePointConnectedVehicleInstantChargingLimit(
                modalChargePointSettingsId
              ).selected == 'soc'
            "
          >
            <i-form-label>Max. SoC</i-form-label>
            <i-number-input
              size="lg"
              class="_text-align:right"
              :min="5"
              :max="100"
              :step="5"
              :model-value="
                mqttStore.getChargePointConnectedVehicleInstantChargingLimit(
                  modalChargePointSettingsId
                ).soc
              "
              @update:model-value="
                setChargePointConnectedVehicleInstantChargingLimitSoc(
                  modalChargePointSettingsId,
                  $event
                )
              "
            >
              <template #suffix>%</template>
            </i-number-input>
          </i-form-group>
          <i-form-group
            v-if="
              mqttStore.getChargePointConnectedVehicleInstantChargingLimit(
                modalChargePointSettingsId
              ).selected == 'amount'
            "
          >
            <i-form-label>Max. Energie</i-form-label>
            <i-number-input
              size="lg"
              class="_text-align:right"
              :min="1"
              :max="100"
              :model-value="
                mqttStore.getChargePointConnectedVehicleInstantChargingLimit(
                  modalChargePointSettingsId
                ).amount / 1000
              "
              @update:model-value="
                setChargePointConnectedVehicleInstantChargingLimitAmount(
                  modalChargePointSettingsId,
                  $event * 1000
                )
              "
            >
              <template #suffix>kWh</template>
            </i-number-input>
          </i-form-group>
        </i-form>
      </i-tab>
      <i-tab name="tab-pv-charging">
        <i-form>
          <i-form-group inline>
            <i-form-label placement="left" class="_align-items:center">
              Einspeisegrenze beachten
            </i-form-label>
            <i-toggle
              size="lg"
              :model-value="
                mqttStore.getChargePointConnectedVehiclePvChargingFeedInLimit(
                  modalChargePointSettingsId
                )
              "
              @update:model-value="
                setChargePointConnectedVehiclePvChargingFeedInLimit(
                  modalChargePointSettingsId,
                  $event
                )
              "
            />
          </i-form-group>
          <i-form-group>
            <i-form-label>Minimal Stromstärke</i-form-label>
            <i-number-input
              size="lg"
              class="_text-align:right"
              id="pv-min-current"
              :min="6"
              :max="32"
              :model-value="
                mqttStore.getChargePointConnectedVehiclePvChargingMinCurrent(
                  modalChargePointSettingsId
                )
              "
              @update:model-value="
                setChargePointConnectedVehiclePvChargingMinCurrent(
                  modalChargePointSettingsId,
                  $event
                )
              "
            >
              <template #suffix>A</template>
            </i-number-input>
          </i-form-group>
          <i-form-group>
            <i-form-label>Minimal SoC</i-form-label>
            <i-number-input
              size="lg"
              class="_text-align:right"
              id="pv-min-soc"
              :min="0"
              :max="95"
              :step="5"
              :model-value="
                mqttStore.getChargePointConnectedVehiclePvChargingMinSoc(
                  modalChargePointSettingsId
                )
              "
              @update:model-value="
                setChargePointConnectedVehiclePvChargingMinSoc(
                  modalChargePointSettingsId,
                  $event
                )
              "
            >
              <template #suffix>%</template>
            </i-number-input>
          </i-form-group>
          <i-form-group>
            <i-form-label>Minimal SoC Stromstärke</i-form-label>
            <i-number-input
              size="lg"
              class="_text-align:right"
              id="pv-min-soc-current"
              :min="6"
              :max="32"
              :model-value="
                mqttStore.getChargePointConnectedVehiclePvChargingMinSocCurrent(
                  modalChargePointSettingsId
                )
              "
              @update:model-value="
                setChargePointConnectedVehiclePvChargingMinSocCurrent(
                  modalChargePointSettingsId,
                  $event
                )
              "
            >
              <template #suffix>A</template>
            </i-number-input>
          </i-form-group>
          <i-form-group>
            <i-form-label>Maximal SoC</i-form-label>
            <i-number-input
              size="lg"
              class="_text-align:right"
              id="pv-max-soc"
              :min="5"
              :max="100"
              :step="5"
              :model-value="
                mqttStore.getChargePointConnectedVehiclePvChargingMaxSoc(
                  modalChargePointSettingsId
                )
              "
              @update:model-value="
                setChargePointConnectedVehiclePvChargingMaxSoc(
                  modalChargePointSettingsId,
                  $event
                )
              "
            >
              <template #suffix>%</template>
            </i-number-input>
          </i-form-group>
        </i-form>
      </i-tab>
      <i-tab name="tab-scheduled-charging">
        <i-form>
          <i-form-group>
            <i-form-label> </i-form-label>
          </i-form-group>
        </i-form>
      </i-tab>
      <i-tab name="tab-time-charging">
        <i-form>
          <i-form-group>
            <i-form-label> </i-form-label>
          </i-form-group>
        </i-form>
      </i-tab>
    </i-tabs>
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

:deep(.toggle .toggle-label::before) {
  border-color: var(--color--dark-45);
}
.badge.full-width {
  width: 100%;
}

:deep(.tab) {
  min-height: 75vh;
  max-height: 75vh;
  overflow-y: scroll;
}

:deep(.input-prepend),
:deep(.input-append) {
  min-width: 3em;
}
</style>
