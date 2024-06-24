<script>
import { useMqttStore } from "@/stores/mqtt.js";
import DashBoardCard from "@/components/DashBoardCard.vue";
import SparkLine from "@/components/SparkLine.vue";
import ChargePointPlugBadge from "@/components/ChargePointPlugBadge.vue";
import ChargePointLockButton from "@/components/ChargePointLockButton.vue";
import ChargePointCodeButton from "@/components/ChargePointCodeButton.vue";
import ExtendedNumberInput from "@/components/ExtendedNumberInput.vue";
import ManualSocInput from "@/components/ChargePoints/ManualSocInput.vue";

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
  faEdit as fasEdit,
  faTimesCircle as fasTimesCircle,
  faExclamationTriangle as fasExclamationTriangle,
  faInfoCircle as fasInfoCircle,
  faStar as fasStar,
  faClock as fasClock,
  faBolt as fasBolt,
  faCalendarDay as fasCalendarDay,
  faCalendarWeek as fasCalendarWeek,
  faCalendarAlt as fasCalendarAlt,
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
  fasEdit,
  fasTimesCircle,
  fasExclamationTriangle,
  fasInfoCircle,
  fasStar,
  farStar,
  fasClock,
  farClock,
  fasBolt,
  fasCalendarDay,
  fasCalendarWeek,
  fasCalendarAlt,
);

export default {
  name: "ChargePointsView",
  data() {
    return {
      mqttStore: useMqttStore(),
      modalChargeModeSettingVisible: false,
      modalVehicleSelectVisible: false,
      modalChargePointSettingsVisible: false,
      modalChargePointId: 0,
      modalVehicleId: 0,
      modalActiveTab: "tab-general",
      modalManualSocInputVisible: false,
    };
  },
  props: {
    changesLocked: { required: false, type: Boolean, default: false },
  },
  components: {
    DashBoardCard,
    SparkLine,
    ChargePointPlugBadge,
    ChargePointLockButton,
    ChargePointCodeButton,
    ExtendedNumberInput,
    ManualSocInput,
    FontAwesomeIcon,
  },
  watch: {
    changesLocked(newValue, oldValue) {
      // hide all modals if lock is kicking in
      if (oldValue !== true && newValue === true) {
        this.modalChargeModeSettingVisible = false;
        this.modalVehicleSelectVisible = false;
        this.modalChargePointSettingsVisible = false;
        this.modalManualSocInputVisible = false;
      }
    },
  },
  computed: {
    vehicleList() {
      let topicList = this.mqttStore.getVehicleList;
      /* topicList is an object, but we need an array for our select input */
      var vehicleList = [];
      Object.keys(topicList).forEach((topic) => {
        let id = parseInt(
          topic.match(/(?:\/)([0-9]+)(?=\/)*/g)[0].replace(/[^0-9]+/g, ""),
        );
        vehicleList.push({ id: id, name: topicList[topic] });
      });
      return vehicleList;
    },
  },
  methods: {
    toggleChargePointSettings(id) {
      // reset selected tab to active charge mode settings
      switch (
        this.mqttStore.getChargePointConnectedVehicleChargeMode(id).mode
      ) {
        case "pv_charging":
          this.modalActiveTab = "tab-pv-charging";
          break;
        case "scheduled_charging":
          this.modalActiveTab = "tab-scheduled-charging";
          break;
        default:
          this.modalActiveTab = "tab-instant-charging";
      }
      this.modalChargePointId = id;
      this.modalChargePointSettingsVisible = true;
    },
    handleChargeModeClick(chargePointId) {
      if (!this.changesLocked) {
        this.modalChargePointId = chargePointId;
        this.modalChargeModeSettingVisible = true;
      }
    },
    handleVehicleClick(chargePointId) {
      if (
        !this.changesLocked &&
        this.mqttStore.getChargePointVehicleChangePermitted(chargePointId)
      ) {
        this.modalChargePointId = chargePointId;
        this.modalVehicleSelectVisible = true;
      }
    },
    handleSocClick(id) {
      let vehicle_id = this.mqttStore.getChargePointConnectedVehicleId(id);
      if (this.mqttStore.getVehicleSocIsManual(vehicle_id)) {
        this.modalVehicleId = vehicle_id;
        this.modalManualSocInputVisible = true;
        return;
      }
      this.$root.sendTopicToBroker(
        `openWB/set/vehicle/${vehicle_id}/get/force_soc_update`,
        1,
      );
    },
    setChargePointConnectedVehicle(id, event) {
      if (event.id != this.mqttStore.getChargePointConnectedVehicleId(id)) {
        this.$root.sendTopicToBroker(
          `openWB/chargepoint/${id}/config/ev`,
          event.id,
        );
      }
      // hide modal vehicle select if visible
      if (this.modalVehicleSelectVisible) {
        this.modalVehicleSelectVisible = false;
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
          event,
        );
      }
    },
    setChargePointConnectedVehiclePriority(id, event) {
      if (event != this.mqttStore.getChargePointConnectedVehiclePriority(id)) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/prio`,
          event,
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
          event,
        );
      }
    },
    setChargePointConnectedVehicleInstantChargingCurrent(id, event) {
      if (
        event &&
        event !=
          this.mqttStore.getChargePointConnectedVehicleInstantChargingCurrent(
            id,
          )
      ) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/instant_charging/current`,
          parseFloat(event),
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
          selected_limit,
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
          parseInt(soc_limit),
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
          amount_limit,
        );
      }
    },
    setChargePointConnectedVehiclePvChargingFeedInLimit(id, event) {
      if (
        event !=
        this.mqttStore.getChargePointConnectedVehiclePvChargingFeedInLimit(id)
      ) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/pv_charging/feed_in_limit`,
          event,
        );
      }
    },
    setChargePointConnectedVehiclePvChargingMinCurrent(id, event) {
      let previous_value =
        this.mqttStore.getChargePointConnectedVehiclePvChargingMinCurrent(id);
      let new_value = parseInt(event);
      if (new_value != previous_value && !isNaN(new_value)) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/pv_charging/min_current`,
          new_value,
        );
      }
    },
    setChargePointConnectedVehiclePvChargingMinSoc(id, soc) {
      let previous_value =
        this.mqttStore.getChargePointConnectedVehiclePvChargingMinSoc(id);
      let new_value = parseInt(soc);
      if (new_value != previous_value && !isNaN(new_value)) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/pv_charging/min_soc`,
          new_value,
        );
      }
    },
    setChargePointConnectedVehiclePvChargingMinSocCurrent(id, event) {
      let previous_value =
        this.mqttStore.getChargePointConnectedVehiclePvChargingMinSocCurrent(
          id,
        );
      let new_value = parseInt(event);
      if (new_value != previous_value && !isNaN(new_value)) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/pv_charging/min_soc_current`,
          new_value,
        );
      }
    },
    setChargePointConnectedVehiclePvChargingMaxSoc(id, soc) {
      let previous_value =
        this.mqttStore.getChargePointConnectedVehiclePvChargingMaxSoc(id);
      let new_value = parseInt(soc);
      if (new_value != previous_value && !isNaN(new_value)) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/pv_charging/max_soc`,
          new_value,
        );
      }
    },
    setChargePointConnectedVehicleScheduledChargingPlanActive(
      plan_key,
      active,
    ) {
      this.$root.sendTopicToBroker(`${plan_key}/active`, active);
    },
    setChargePointConnectedVehicleTimeChargingPlanActive(plan_key, active) {
      this.$root.sendTopicToBroker(`${plan_key}/active`, active);
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
        <charge-point-plug-badge :chargePointId="[id]" />
      </template>
      <i-container>
        <i-row>
          <!-- charge point data on left side -->
          <i-column>
            <i-row>
              <i-column class="_padding-left:0 _padding-right:0">
                <charge-point-code-button
                  v-if="mqttStore.getRfidEnabled"
                  :chargePointId="id"
                />
                <charge-point-lock-button
                  :chargePointId="id"
                  :changesLocked="changesLocked"
                />
              </i-column>
              <i-column class="_text-align:right _padding-left:0">
                {{ mqttStore.getChargePointPower(id) }}
                {{ mqttStore.getChargePointPhasesInUse(id) }}
                {{ mqttStore.getChargePointSetCurrent(id) }}
              </i-column>
            </i-row>
            <i-row class="_padding-top:1">
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
                <i-badge
                  size="lg"
                  class="full-width"
                  :class="!changesLocked ? 'clickable' : ''"
                  :disabled="
                    !mqttStore.getChargePointVehicleChangePermitted(
                      modalChargePointId,
                    )
                  "
                  @click="handleVehicleClick(id)"
                >
                  <font-awesome-icon fixed-width :icon="['fas', 'fa-car']" />
                  {{ mqttStore.getChargePointConnectedVehicleName(id) }}
                </i-badge>
              </i-column>
              <i-column
                v-if="
                  mqttStore.getVehicleSocConfigured(
                    mqttStore.getChargePointConnectedVehicleId(id),
                  ) ||
                  mqttStore.getVehicleFaultState(
                    mqttStore.getChargePointConnectedVehicleId(id),
                  ) != 0
                "
                class="_flex-grow:0 _padding-right:0 _padding-left:1"
              >
                <i-button
                  size="sm"
                  :disabled="changesLocked"
                  :class="!changesLocked ? 'clickable' : ''"
                  @click="handleSocClick(id)"
                >
                  <span
                    v-if="
                      mqttStore.getVehicleSocConfigured(
                        mqttStore.getChargePointConnectedVehicleId(id),
                      )
                    "
                  >
                    <font-awesome-icon
                      fixed-width
                      :icon="
                        mqttStore.getVehicleSocIsManual(
                          mqttStore.getChargePointConnectedVehicleId(id),
                        )
                          ? ['fas', 'fa-edit']
                          : ['fas', 'fa-car-battery']
                      "
                    />
                    {{ mqttStore.getChargePointConnectedVehicleSoc(id).soc }}%
                  </span>
                  <font-awesome-icon
                    v-if="
                      mqttStore.getVehicleFaultState(
                        mqttStore.getChargePointConnectedVehicleId(id),
                      ) != 0
                    "
                    fixed-width
                    :icon="
                      mqttStore.getVehicleFaultState(
                        mqttStore.getChargePointConnectedVehicleId(id),
                      ) > 0
                        ? mqttStore.getVehicleFaultState(
                            mqttStore.getChargePointConnectedVehicleId(id),
                          ) > 1
                          ? ['fas', 'times-circle']
                          : ['fas', 'exclamation-triangle']
                        : []
                    "
                    :class="
                      mqttStore.getVehicleFaultState(
                        mqttStore.getChargePointConnectedVehicleId(id),
                      ) > 0
                        ? mqttStore.getVehicleFaultState(
                            mqttStore.getChargePointConnectedVehicleId(id),
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
                  class="full-width"
                  :class="!changesLocked ? 'clickable' : ''"
                  :color="
                    mqttStore.getChargePointConnectedVehicleChargeMode(id).class
                  "
                  @click="handleChargeModeClick(id)"
                >
                  {{
                    mqttStore.getChargePointConnectedVehicleChargeMode(id).label
                  }}
                  <font-awesome-icon
                    fixed-width
                    :icon="
                      mqttStore.getChargePointConnectedVehiclePriority(id)
                        ? ['fas', 'fa-star']
                        : ['far', 'fa-star']
                    "
                    :class="
                      mqttStore.getChargePointConnectedVehiclePriority(id)
                        ? '_color:warning'
                        : ''
                    "
                  />
                </i-badge>
              </i-column>
              <i-column
                v-if="
                  mqttStore.getChargePointConnectedVehicleTimeChargingActive(id)
                "
                class="_flex-grow:0 _padding-right:0 _padding-left:1"
              >
                <i-badge size="lg">
                  <font-awesome-icon
                    v-if="
                      mqttStore.getChargePointConnectedVehicleTimeChargingActive(
                        id,
                      )
                    "
                    fixed-width
                    :icon="
                      mqttStore.getChargePointConnectedVehicleTimeChargingRunning(
                        id,
                      )
                        ? ['fas', 'fa-clock']
                        : ['far', 'fa-clock']
                    "
                    :class="
                      mqttStore.getChargePointConnectedVehicleTimeChargingRunning(
                        id,
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
  <!-- charge mode only -->
  <i-modal v-model="modalChargeModeSettingVisible" size="lg">
    <template #header>
      Lademodus für "{{
        mqttStore.getChargePointConnectedVehicleName(modalChargePointId)
      }}" auswählen
    </template>
    <i-form>
      <i-form-group>
        <i-form-label>Lademodus</i-form-label>
        <i-button-group block>
          <i-button
            v-for="mode in mqttStore.chargeModeList()"
            :key="mode.id"
            outline
            :color="mode.class != 'dark' ? mode.class : 'light'"
            :active="
              mqttStore.getChargePointConnectedVehicleChargeMode(
                modalChargePointId,
              ) != undefined &&
              mode.id ==
                mqttStore.getChargePointConnectedVehicleChargeMode(
                  modalChargePointId,
                ).mode
            "
            @click="
              setChargePointConnectedVehicleChargeMode(
                modalChargePointId,
                mode.id,
              )
            "
          >
            {{ mode.label }}
          </i-button>
        </i-button-group>
      </i-form-group>
      <i-form-group>
        <i-form-label>Priorität</i-form-label>
        <i-button-group block>
          <i-button
            :color="
              mqttStore.getChargePointConnectedVehiclePriority(
                modalChargePointId,
              ) !== true
                ? 'danger'
                : ''
            "
            @click="
              setChargePointConnectedVehiclePriority(modalChargePointId, false)
            "
          >
            Nein
          </i-button>
          <i-button
            :color="
              mqttStore.getChargePointConnectedVehiclePriority(
                modalChargePointId,
              ) === true
                ? 'success'
                : ''
            "
            @click="
              setChargePointConnectedVehiclePriority(modalChargePointId, true)
            "
          >
            Ja
          </i-button>
        </i-button-group>
      </i-form-group>
    </i-form>
  </i-modal>
  <!-- end charge mode only-->
  <!-- vehicle only -->
  <i-modal
    class="modal-vehicle-select"
    v-model="modalVehicleSelectVisible"
    size="lg"
  >
    <template #header>
      Fahrzeug an "{{ mqttStore.getChargePointName(modalChargePointId) }}"
      auswählen
    </template>
    <i-form>
      <i-form-group>
        <i-button-group vertical block>
          <i-button
            v-for="vehicle in vehicleList"
            :key="vehicle.id"
            :active="
              mqttStore.getChargePointConnectedVehicleId(modalChargePointId) ==
              vehicle.id
            "
            :color="
              mqttStore.getChargePointConnectedVehicleId(modalChargePointId) ==
              vehicle.id
                ? 'primary'
                : ''
            "
            @click="setChargePointConnectedVehicle(modalChargePointId, vehicle)"
          >
            {{ vehicle.name }}
          </i-button>
        </i-button-group>
      </i-form-group>
    </i-form>
  </i-modal>
  <!-- end vehicle only-->
  <!-- charge point settings -->
  <i-modal v-model="modalChargePointSettingsVisible" size="lg">
    <template #header>
      Einstellungen für Ladepunkt "{{
        mqttStore.getChargePointName(modalChargePointId)
      }}"
    </template>
    <i-tabs v-model="modalActiveTab" stretch>
      <template #header>
        <i-tab-title for="tab-instant-charging"> Sofort </i-tab-title>
        <i-tab-title for="tab-pv-charging"> PV </i-tab-title>
        <i-tab-title for="tab-scheduled-charging"> Zielladen </i-tab-title>
        <i-tab-title for="tab-time-charging"> Zeitladen </i-tab-title>
      </template>

      <i-tab name="tab-instant-charging">
        <i-form>
          <i-form-group>
            <i-form-label>Stromstärke</i-form-label>
            <extended-number-input
              unit="A"
              :min="6"
              :max="32"
              :model-value="
                mqttStore.getChargePointConnectedVehicleInstantChargingCurrent(
                  modalChargePointId,
                )
              "
              @update:model-value="
                setChargePointConnectedVehicleInstantChargingCurrent(
                  modalChargePointId,
                  $event,
                )
              "
            />
          </i-form-group>
          <i-form-group>
            <i-form-label>Begrenzung</i-form-label>
            <i-button-group block>
              <i-button
                :color="
                  mqttStore.getChargePointConnectedVehicleInstantChargingLimit(
                    modalChargePointId,
                  ).selected == 'none'
                    ? 'primary'
                    : ''
                "
                :active="
                  mqttStore.getChargePointConnectedVehicleInstantChargingLimit(
                    modalChargePointId,
                  ).selected == 'none'
                "
                @click="
                  setChargePointConnectedVehicleInstantChargingLimit(
                    modalChargePointId,
                    'none',
                  )
                "
              >
                Keine
              </i-button>
              <i-button
                :color="
                  mqttStore.getChargePointConnectedVehicleInstantChargingLimit(
                    modalChargePointId,
                  ).selected == 'soc'
                    ? 'primary'
                    : ''
                "
                :active="
                  mqttStore.getChargePointConnectedVehicleInstantChargingLimit(
                    modalChargePointId,
                  ).selected == 'soc'
                "
                @click="
                  setChargePointConnectedVehicleInstantChargingLimit(
                    modalChargePointId,
                    'soc',
                  )
                "
              >
                EV-SoC
              </i-button>
              <i-button
                :color="
                  mqttStore.getChargePointConnectedVehicleInstantChargingLimit(
                    modalChargePointId,
                  ).selected == 'amount'
                    ? 'primary'
                    : ''
                "
                :active="
                  mqttStore.getChargePointConnectedVehicleInstantChargingLimit(
                    modalChargePointId,
                  ).selected == 'amount'
                "
                @click="
                  setChargePointConnectedVehicleInstantChargingLimit(
                    modalChargePointId,
                    'amount',
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
                modalChargePointId,
              ).selected == 'soc'
            "
          >
            <i-form-label>Max. SoC</i-form-label>
            <extended-number-input
              unit="%"
              :min="5"
              :max="100"
              :step="5"
              :model-value="
                mqttStore.getChargePointConnectedVehicleInstantChargingLimit(
                  modalChargePointId,
                ).soc
              "
              @update:model-value="
                setChargePointConnectedVehicleInstantChargingLimitSoc(
                  modalChargePointId,
                  $event,
                )
              "
            />
          </i-form-group>
          <i-form-group
            v-if="
              mqttStore.getChargePointConnectedVehicleInstantChargingLimit(
                modalChargePointId,
              ).selected == 'amount'
            "
          >
            <i-form-label>Max. Energie</i-form-label>
            <extended-number-input
              unit="kWh"
              :min="1"
              :max="100"
              :model-value="
                mqttStore.getChargePointConnectedVehicleInstantChargingLimit(
                  modalChargePointId,
                ).amount / 1000
              "
              @update:model-value="
                setChargePointConnectedVehicleInstantChargingLimitAmount(
                  modalChargePointId,
                  $event * 1000,
                )
              "
            />
          </i-form-group>
        </i-form>
      </i-tab>
      <i-tab name="tab-pv-charging">
        <i-form>
          <i-form-group>
            <i-form-label>Einspeisegrenze beachten</i-form-label>
            <i-button-group block>
              <i-button
                :color="
                  mqttStore.getChargePointConnectedVehiclePvChargingFeedInLimit(
                    modalChargePointId,
                  ) !== true
                    ? 'danger'
                    : ''
                "
                @click="
                  setChargePointConnectedVehiclePvChargingFeedInLimit(
                    modalChargePointId,
                    false,
                  )
                "
              >
                Nein
              </i-button>
              <i-button
                :color="
                  mqttStore.getChargePointConnectedVehiclePvChargingFeedInLimit(
                    modalChargePointId,
                  ) === true
                    ? 'success'
                    : ''
                "
                @click="
                  setChargePointConnectedVehiclePvChargingFeedInLimit(
                    modalChargePointId,
                    true,
                  )
                "
              >
                Ja
              </i-button>
            </i-button-group>
          </i-form-group>
          <i-form-group>
            <i-form-label>Minimaler Dauerstrom</i-form-label>
            <extended-number-input
              unit="A"
              :labels="[
                { label: 'Aus', value: 0 },
                { label: 6, value: 6 },
                { label: 7, value: 7 },
                { label: 8, value: 8 },
                { label: 9, value: 9 },
                { label: 10, value: 10 },
                { label: 11, value: 11 },
                { label: 12, value: 12 },
                { label: 13, value: 13 },
                { label: 14, value: 14 },
                { label: 15, value: 15 },
                { label: 16, value: 16 },
              ]"
              :model-value="
                mqttStore.getChargePointConnectedVehiclePvChargingMinCurrent(
                  modalChargePointId,
                )
              "
              @update:model-value="
                setChargePointConnectedVehiclePvChargingMinCurrent(
                  modalChargePointId,
                  $event,
                )
              "
            />
          </i-form-group>
          <i-form-group>
            <i-form-label>Mindest-SoC</i-form-label>
            <extended-number-input
              unit="%"
              :labels="[
                { label: 'Aus', value: 0 },
                { label: 5, value: 5 },
                { label: 10, value: 10 },
                { label: 15, value: 15 },
                { label: 20, value: 20 },
                { label: 25, value: 25 },
                { label: 30, value: 30 },
                { label: 35, value: 35 },
                { label: 40, value: 40 },
                { label: 45, value: 45 },
                { label: 50, value: 50 },
                { label: 55, value: 55 },
                { label: 60, value: 60 },
                { label: 65, value: 65 },
                { label: 70, value: 70 },
                { label: 75, value: 75 },
                { label: 80, value: 80 },
                { label: 85, value: 85 },
                { label: 90, value: 90 },
                { label: 95, value: 95 },
              ]"
              :model-value="
                mqttStore.getChargePointConnectedVehiclePvChargingMinSoc(
                  modalChargePointId,
                )
              "
              @update:model-value="
                setChargePointConnectedVehiclePvChargingMinSoc(
                  modalChargePointId,
                  $event,
                )
              "
            />
          </i-form-group>
          <i-form-group>
            <i-form-label>Mindest-SoC Strom</i-form-label>
            <extended-number-input
              :min="6"
              :max="32"
              unit="A"
              :model-value="
                mqttStore.getChargePointConnectedVehiclePvChargingMinSocCurrent(
                  modalChargePointId,
                )
              "
              @update:model-value="
                setChargePointConnectedVehiclePvChargingMinSocCurrent(
                  modalChargePointId,
                  $event,
                )
              "
            />
          </i-form-group>
          <i-form-group>
            <i-form-label>SoC-Limit</i-form-label>
            <extended-number-input
              unit="%"
              :labels="[
                { label: 5, value: 5 },
                { label: 10, value: 10 },
                { label: 15, value: 15 },
                { label: 20, value: 20 },
                { label: 25, value: 25 },
                { label: 30, value: 30 },
                { label: 35, value: 35 },
                { label: 40, value: 40 },
                { label: 45, value: 45 },
                { label: 50, value: 50 },
                { label: 55, value: 55 },
                { label: 60, value: 60 },
                { label: 65, value: 65 },
                { label: 70, value: 70 },
                { label: 75, value: 75 },
                { label: 80, value: 80 },
                { label: 85, value: 85 },
                { label: 90, value: 90 },
                { label: 95, value: 95 },
                { label: 100, value: 100 },
                { label: 'Aus', value: 101 },
              ]"
              :model-value="
                mqttStore.getChargePointConnectedVehiclePvChargingMaxSoc(
                  modalChargePointId,
                )
              "
              @update:model-value="
                setChargePointConnectedVehiclePvChargingMaxSoc(
                  modalChargePointId,
                  $event,
                )
              "
            />
          </i-form-group>
        </i-form>
      </i-tab>
      <i-tab name="tab-scheduled-charging">
        <i-alert
          v-if="
            Object.keys(
              mqttStore.getChargePointConnectedVehicleScheduledChargingPlans(
                modalChargePointId,
              ),
            ).length === 0
          "
        >
          <template #icon>
            <font-awesome-icon fixed-width :icon="['fas', 'fa-info-circle']" />
          </template>
          Es wurden noch keine Zeitpläne für das Zielladen eingerichtet.
        </i-alert>
        <i-form v-else>
          <i-form-group
            v-for="(
              plan, planKey
            ) in mqttStore.getChargePointConnectedVehicleScheduledChargingPlans(
              modalChargePointId,
            )"
            :key="planKey"
          >
            <i-container>
              <i-row>
                <i-form-label>{{ plan.name }}</i-form-label>
              </i-row>
              <i-row>
                <i-button
                  size="lg"
                  block
                  :color="plan.active ? 'success' : 'danger'"
                  @click="
                    setChargePointConnectedVehicleScheduledChargingPlanActive(
                      planKey,
                      !plan.active,
                    )
                  "
                >
                  <span v-if="plan.frequency.selected == 'once'">
                    <font-awesome-icon
                      fixed-width
                      :icon="['fas', 'calendar-day']"
                    />
                    {{ mqttStore.formatDate(plan.frequency.once) }}
                  </span>
                  <span v-if="plan.frequency.selected == 'daily'">
                    <font-awesome-icon
                      fixed-width
                      :icon="['fas', 'calendar-week']"
                    />
                    täglich
                  </span>
                  <span v-if="plan.frequency.selected == 'weekly'">
                    <font-awesome-icon
                      fixed-width
                      :icon="['fas', 'calendar-alt']"
                    />
                    {{
                      mqttStore.formatWeeklyScheduleDays(plan.frequency.weekly)
                    }}
                  </span>
                  <font-awesome-icon fixed-width :icon="['fas', 'clock']" />
                  {{ plan.time }}
                  <span v-if="plan.limit.selected == 'soc'">
                    <font-awesome-icon
                      fixed-width
                      :icon="['fas', 'car-battery']"
                    />
                    {{ plan.limit.soc_scheduled }}&nbsp;%
                  </span>
                  <span v-if="plan.limit.selected == 'amount'">
                    <font-awesome-icon fixed-width :icon="['fas', 'bolt']" />
                    {{ plan.limit.amount / 1000 }}&nbsp;kWh
                  </span>
                </i-button>
              </i-row>
            </i-container>
          </i-form-group>
        </i-form>
      </i-tab>
      <i-tab name="tab-time-charging">
        <i-form>
          <i-form-group>
            <i-form-label>Zeitladen aktivieren</i-form-label>
            <i-button-group block>
              <i-button
                :color="
                  mqttStore.getChargePointConnectedVehicleTimeChargingActive(
                    modalChargePointId,
                  ) !== true
                    ? 'danger'
                    : ''
                "
                @click="
                  setChargePointConnectedVehicleTimeChargingActive(
                    modalChargePointId,
                    false,
                  )
                "
              >
                Nein
              </i-button>
              <i-button
                :color="
                  mqttStore.getChargePointConnectedVehicleTimeChargingActive(
                    modalChargePointId,
                  ) === true
                    ? 'success'
                    : ''
                "
                @click="
                  setChargePointConnectedVehicleTimeChargingActive(
                    modalChargePointId,
                    true,
                  )
                "
              >
                Ja
              </i-button>
            </i-button-group>
          </i-form-group>
          <div
            v-if="
              mqttStore.getChargePointConnectedVehicleTimeChargingActive(
                modalChargePointId,
              ) === true
            "
          >
            <i-alert
              v-if="
                Object.keys(
                  mqttStore.getChargePointConnectedVehicleTimeChargingPlans(
                    modalChargePointId,
                  ),
                ).length === 0
              "
              color="warning"
              class="_margin-top:2"
            >
              <template #icon>
                <font-awesome-icon
                  fixed-width
                  :icon="['fas', 'fa-circle-info']"
                />
              </template>
              Es wurden noch keine Zeitpläne für das Zeitladen eingerichtet.
            </i-alert>
            <div v-else>
              <i-form-group
                v-for="(
                  plan, planKey
                ) in mqttStore.getChargePointConnectedVehicleTimeChargingPlans(
                  modalChargePointId,
                )"
                :key="planKey"
              >
                <i-container>
                  <i-row>
                    <i-form-label>{{ plan.name }}</i-form-label>
                  </i-row>
                  <i-row>
                    <i-button
                      size="lg"
                      block
                      :color="plan.active ? 'success' : 'danger'"
                      @click="
                        setChargePointConnectedVehicleTimeChargingPlanActive(
                          planKey,
                          !plan.active,
                        )
                      "
                    >
                      <span v-if="plan.frequency.selected == 'once'">
                        <font-awesome-icon
                          fixed-width
                          :icon="['fas', 'calendar-day']"
                        />
                        {{ mqttStore.formatDateRange(plan.frequency.once) }}
                      </span>
                      <span v-if="plan.frequency.selected == 'daily'">
                        <font-awesome-icon
                          fixed-width
                          :icon="['fas', 'calendar-week']"
                        />
                        täglich
                      </span>
                      <span v-if="plan.frequency.selected == 'weekly'">
                        <font-awesome-icon
                          fixed-width
                          :icon="['fas', 'calendar-alt']"
                        />
                        {{
                          mqttStore.formatWeeklyScheduleDays(
                            plan.frequency.weekly,
                          )
                        }}
                      </span>
                      <font-awesome-icon fixed-width :icon="['fas', 'clock']" />
                      {{ plan.time.join("-") }}
                      <span v-if="plan.limit.selected == 'soc'">
                        <font-awesome-icon
                          fixed-width
                          :icon="['fas', 'car-battery']"
                        />
                        {{ plan.limit.soc }}&nbsp;%
                      </span>
                      <span v-if="plan.limit.selected == 'amount'">
                        <font-awesome-icon
                          fixed-width
                          :icon="['fas', 'bolt']"
                        />
                        {{ plan.limit.amount / 1000 }}&nbsp;kWh
                      </span>
                    </i-button>
                  </i-row>
                </i-container>
              </i-form-group>
            </div>
          </div>
        </i-form>
      </i-tab>
    </i-tabs>
  </i-modal>
  <!-- end charge point settings modal-->
  <!-- manual soc input -->
  <manual-soc-input
    :vehicleId="modalVehicleId"
    v-model="modalManualSocInputVisible"
  />
  <!-- end manual soc input -->
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

.clickable {
  cursor: pointer;
}

:deep(.tab) {
  min-height: 72vh;
  max-height: 72vh;
  overflow-y: scroll;
}

.modal-vehicle-select:deep(.modal-body) {
  max-height: 72vh;
  overflow-y: scroll;
}

:deep(.input-prepend),
:deep(.input-append) {
  min-width: 3em;
}
</style>
