<script>
import { useMqttStore } from "@/stores/mqtt.js";
import ChargePointCard from "@/components/ChargePoints/ChargePointCard.vue";
import SimpleChargePointCard from "@/components/ChargePoints/SimpleChargePointCard.vue";
import ExtendedNumberInput from "@/components/ExtendedNumberInput.vue";
import ManualSocInput from "@/components/ChargePoints/ManualSocInput.vue";

/* fontawesome */
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import {
  faBolt as fasBolt,
  faCalendarDay as fasCalendarDay,
  faCalendarWeek as fasCalendarWeek,
  faCalendarAlt as fasCalendarAlt,
  faCoins as fasCoins,
} from "@fortawesome/free-solid-svg-icons";
/* add icons to the library */
library.add(
  fasBolt,
  fasCalendarDay,
  fasCalendarWeek,
  fasCalendarAlt,
  fasCoins,
);

export default {
  name: "ChargePointsView",
  components: {
    ChargePointCard,
    SimpleChargePointCard,
    ExtendedNumberInput,
    ManualSocInput,
    FontAwesomeIcon,
  },
  props: {
    changesLocked: { required: false, type: Boolean, default: false },
  },
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
      simpleChargeModes: [
        "instant_charging",
        "pv_charging",
        "stop",
      ]
    };
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
    filteredChargeModes() {
      if (this.mqttStore.getSimpleChargePointView) {
        return this.mqttStore.chargeModeList().filter((mode) => {
          return this.simpleChargeModes.includes(mode.id);
        });
      }
      return this.mqttStore.chargeModeList()
    },
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
        case "eco_charging":
          this.modalActiveTab = "tab-eco-charging";
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
      if (!this.changesLocked) {
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
    setChargePointConnectedVehicleInstantChargingPhases(id, selected_phases) {
      if (
        selected_phases &&
        selected_phases !=
          this.mqttStore.getChargePointConnectedVehicleInstantChargingPhases(id)
      ) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/instant_charging/phases_to_use`,
          selected_phases,
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
    setChargePointConnectedVehiclePvChargingPhases(id, selected_phases) {
      if (
        selected_phases &&
        selected_phases !=
          this.mqttStore.getChargePointConnectedVehiclePvChargingPhases(id)
      ) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/pv_charging/phases_to_use`,
          selected_phases,
        );
      }
    },
    setChargePointConnectedVehiclePvChargingLimit(id, selected_limit) {
      if (
        selected_limit &&
        selected_limit !=
          this.mqttStore.getChargePointConnectedVehiclePvChargingLimit(id)
            .selected
      ) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/pv_charging/limit/selected`,
          selected_limit,
        );
      }
    },
    setChargePointConnectedVehiclePvChargingLimitSoc(id, soc_limit) {
      if (
        soc_limit &&
        soc_limit !=
          this.mqttStore.getChargePointConnectedVehiclePvChargingLimit(id)
            .soc
      ) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/pv_charging/limit/soc`,
          parseInt(soc_limit),
        );
      }
    },
    setChargePointConnectedVehiclePvChargingLimitAmount(id, amount_limit) {
      if (
        amount_limit &&
        amount_limit !=
          this.mqttStore.getChargePointConnectedVehiclePvChargingLimit(id)
            .amount
      ) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/pv_charging/limit/amount`,
          amount_limit,
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
    setChargePointConnectedVehiclePvChargingMinSocPhases(id, selected_phases) {
      if (
        selected_phases &&
        selected_phases !=
          this.mqttStore.getChargePointConnectedVehiclePvChargingMinSocPhases(id)
      ) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/pv_charging/phases_to_use_min_soc`,
          selected_phases,
        );
      }
    },
    setChargePointConnectedVehicleEcoChargingCurrent(id, event) {
      let previous_value =
        this.mqttStore.getChargePointConnectedVehicleEcoChargingCurrent(id);
      let new_value = parseInt(event);
      if (new_value != previous_value && !isNaN(new_value)) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/eco_charging/current`,
          new_value,
        );
      }
    },
    setChargePointConnectedVehicleEcoChargingPhases(id, selected_phases) {
      if (
        selected_phases &&
        selected_phases !=
          this.mqttStore.getChargePointConnectedVehicleEcoChargingPhases(id)
      ) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/eco_charging/phases_to_use`,
          selected_phases,
        );
      }
    },
    setChargePointConnectedVehicleEcoChargingLimit(id, selected_limit) {
      if (
        selected_limit &&
        selected_limit !=
          this.mqttStore.getChargePointConnectedVehicleEcoChargingLimit(id)
            .selected
      ) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/eco_charging/limit/selected`,
          selected_limit,
        );
      }
    },
    setChargePointConnectedVehicleEcoChargingLimitSoc(id, soc_limit) {
      if (
        soc_limit &&
        soc_limit !=
          this.mqttStore.getChargePointConnectedVehicleEcoChargingLimit(id)
            .soc
      ) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/eco_charging/limit/soc`,
          parseInt(soc_limit),
        );
      }
    },
    setChargePointConnectedVehicleEcoChargingLimitAmount(id, amount_limit) {
      if (
        amount_limit &&
        amount_limit !=
          this.mqttStore.getChargePointConnectedVehicleEcoChargingLimit(id)
            .amount
      ) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/eco_charging/limit/amount`,
          amount_limit,
        );
      }
    },
    setChargePointConnectedVehicleEcoChargingMaxPrice(id, event) {
      let previous_value =
        this.mqttStore.getChargePointConnectedVehicleEcoChargingMaxPrice(id);
      let new_value = parseInt(event);
      if (new_value != previous_value && !isNaN(new_value)) {
        var template_id =
          this.mqttStore.getChargePointConnectedVehicleChargeTemplateIndex(id);
        this.$root.sendTopicToBroker(
          `openWB/vehicle/template/charge_template/${template_id}/chargemode/eco_charging/max_price`,
          parseFloat((new_value / 100000).toFixed(7)),
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
    <component
      :is="mqttStore.getSimpleChargePointView ? 'SimpleChargePointCard' : 'ChargePointCard'"
      v-for="id in mqttStore.getChargePointIds"
      :key="id"
      :charge-point-id="id"
      :changes-locked="changesLocked"
      @vehicle-click="handleVehicleClick"
      @soc-click="handleSocClick"
      @charge-mode-click="handleChargeModeClick"
      @toggle-charge-point-settings="toggleChargePointSettings"
      @set-charge-point-connected-vehicle-charge-mode="setChargePointConnectedVehicleChargeMode"
    />
  </div>
  <!-- modals -->
  <!-- charge mode only -->
  <i-modal
    v-model="modalChargeModeSettingVisible"
    size="lg"
  >
    <template #header>
      Lademodus für "{{
        mqttStore.getChargePointConnectedVehicleName(modalChargePointId)
      }}" auswählen
    </template>
    <i-form>
      <i-form-group>
        <i-button-group
          block
          vertical
        >
          <i-button
            v-for="mode in filteredChargeModes"
            :key="mode.id"
            size="lg"
            class="large-button"
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
            size="lg"
            class="large-button"
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
    v-model="modalVehicleSelectVisible"
    class="modal-vehicle-select"
    size="lg"
  >
    <template #header>
      Fahrzeug an "{{ mqttStore.getChargePointName(modalChargePointId) }}"
      auswählen
    </template>
    <i-form>
      <i-form-group>
        <i-button-group
          vertical
          block
        >
          <i-button
            v-for="vehicle in vehicleList"
            :key="vehicle.id"
            size="lg"
            class="large-button"
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
  <i-modal
    v-model="modalChargePointSettingsVisible"
    size="lg"
  >
    <template #header>
      Einstellungen für Fahrzeug "{{
        mqttStore.getChargePointConnectedVehicleName(modalChargePointId)
      }}"
    </template>
    <i-tabs
      v-model="modalActiveTab"
      stretch
    >
      <template #header>
        <i-tab-title for="tab-instant-charging">
          Sofort
        </i-tab-title>
        <i-tab-title for="tab-pv-charging">
          PV
        </i-tab-title>
        <i-tab-title
          v-if="!mqttStore.getSimpleChargePointView"
          for="tab-eco-charging"
        >
          Eco
        </i-tab-title>
        <i-tab-title
          v-if="!mqttStore.getSimpleChargePointView"
          for="tab-scheduled-charging"
        >
          Ziel
        </i-tab-title>
        <i-tab-title
          v-if="!mqttStore.getSimpleChargePointView"
          for="tab-time-charging"
        >
          Zeit
        </i-tab-title>
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
            <i-form-label>Anzahl Phasen</i-form-label>
            <i-button-group block>
              <i-button
                :color="
                  mqttStore.getChargePointConnectedVehicleInstantChargingPhases(
                    modalChargePointId,
                  ) == 1
                    ? 'primary'
                    : ''
                "
                :active="
                  mqttStore.getChargePointConnectedVehicleInstantChargingPhases(
                    modalChargePointId,
                  ) == 1
                "
                @click="
                  setChargePointConnectedVehicleInstantChargingPhases(
                    modalChargePointId,
                    1,
                  )
                "
              >
                1
              </i-button>
              <i-button
                :color="
                  mqttStore.getChargePointConnectedVehicleInstantChargingPhases(
                    modalChargePointId,
                  ) == 3
                    ? 'primary'
                    : ''
                "
                :active="
                  mqttStore.getChargePointConnectedVehicleInstantChargingPhases(
                    modalChargePointId,
                  ) == 3
                "
                @click="
                  setChargePointConnectedVehicleInstantChargingPhases(
                    modalChargePointId,
                    3,
                  )
                "
              >
                Maximum
              </i-button>
            </i-button-group>
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
                Aus
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
            <i-form-label>Anzahl Phasen</i-form-label>
            <i-button-group block>
              <i-button
                :color="
                  mqttStore.getChargePointConnectedVehiclePvChargingPhases(
                    modalChargePointId,
                  ) == 1
                    ? 'primary'
                    : ''
                "
                :active="
                  mqttStore.getChargePointConnectedVehiclePvChargingPhases(
                    modalChargePointId,
                  ) == 1
                "
                @click="
                  setChargePointConnectedVehiclePvChargingPhases(
                    modalChargePointId,
                    1,
                  )
                "
              >
                1
              </i-button>
              <i-button
                :color="
                  mqttStore.getChargePointConnectedVehiclePvChargingPhases(
                    modalChargePointId,
                  ) == 3
                    ? 'primary'
                    : ''
                "
                :active="
                  mqttStore.getChargePointConnectedVehiclePvChargingPhases(
                    modalChargePointId,
                  ) == 3
                "
                @click="
                  setChargePointConnectedVehiclePvChargingPhases(
                    modalChargePointId,
                    3,
                  )
                "
              >
                Maximum
              </i-button>
              <i-button
                :color="
                  mqttStore.getChargePointConnectedVehiclePvChargingPhases(
                    modalChargePointId,
                  ) == 0
                    ? 'primary'
                    : ''
                "
                :active="
                  mqttStore.getChargePointConnectedVehiclePvChargingPhases(
                    modalChargePointId,
                  ) == 0
                "
                @click="
                  setChargePointConnectedVehiclePvChargingPhases(
                    modalChargePointId,
                    0,
                  )
                "
              >
                Automatik
              </i-button>
            </i-button-group>
          </i-form-group>
          <i-form-group>
            <i-form-label>Begrenzung</i-form-label>
            <i-button-group block>
              <i-button
                :color="
                  mqttStore.getChargePointConnectedVehiclePvChargingLimit(
                    modalChargePointId,
                  ).selected == 'none'
                    ? 'primary'
                    : ''
                "
                :active="
                  mqttStore.getChargePointConnectedVehiclePvChargingLimit(
                    modalChargePointId,
                  ).selected == 'none'
                "
                @click="
                  setChargePointConnectedVehiclePvChargingLimit(
                    modalChargePointId,
                    'none',
                  )
                "
              >
                Aus
              </i-button>
              <i-button
                :color="
                  mqttStore.getChargePointConnectedVehiclePvChargingLimit(
                    modalChargePointId,
                  ).selected == 'soc'
                    ? 'primary'
                    : ''
                "
                :active="
                  mqttStore.getChargePointConnectedVehiclePvChargingLimit(
                    modalChargePointId,
                  ).selected == 'soc'
                "
                @click="
                  setChargePointConnectedVehiclePvChargingLimit(
                    modalChargePointId,
                    'soc',
                  )
                "
              >
                EV-SoC
              </i-button>
              <i-button
                :color="
                  mqttStore.getChargePointConnectedVehiclePvChargingLimit(
                    modalChargePointId,
                  ).selected == 'amount'
                    ? 'primary'
                    : ''
                "
                :active="
                  mqttStore.getChargePointConnectedVehiclePvChargingLimit(
                    modalChargePointId,
                  ).selected == 'amount'
                "
                @click="
                  setChargePointConnectedVehiclePvChargingLimit(
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
              mqttStore.getChargePointConnectedVehiclePvChargingLimit(
                modalChargePointId,
              ).selected == 'soc'
            "
          >
            <i-form-label>SoC-Limit für das Fahrzeug</i-form-label>
            <extended-number-input
              unit="%"
              :min="5"
              :max="100"
              :step="5"
              :model-value="
                mqttStore.getChargePointConnectedVehiclePvChargingLimit(
                  modalChargePointId,
                ).soc
              "
              @update:model-value="
                setChargePointConnectedVehiclePvChargingLimitSoc(
                  modalChargePointId,
                  $event,
                )
              "
            />
          </i-form-group>
          <i-form-group
            v-if="
              mqttStore.getChargePointConnectedVehiclePvChargingLimit(
                modalChargePointId,
              ).selected == 'amount'
            "
          >
            <i-form-label>Energie-Limit</i-form-label>
            <extended-number-input
              unit="kWh"
              :min="1"
              :max="100"
              :model-value="
                mqttStore.getChargePointConnectedVehiclePvChargingLimit(
                  modalChargePointId,
                ).amount / 1000
              "
              @update:model-value="
                setChargePointConnectedVehiclePvChargingLimitAmount(
                  modalChargePointId,
                  $event * 1000,
                )
              "
            />
          </i-form-group>
          <i-form-group>
            <i-form-label>Mindest-SoC für das Fahrzeug</i-form-label>
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
          <i-form-group
            v-if="mqttStore.getChargePointConnectedVehiclePvChargingMinSoc(
              modalChargePointId,
            ) > 0"
          >
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
          <i-form-group
            v-if="mqttStore.getChargePointConnectedVehiclePvChargingMinSoc(
              modalChargePointId,
            ) > 0"
          >
            <i-form-label>Anzahl Phasen Mindest-SoC</i-form-label>
            <i-button-group block>
              <i-button
                :color="
                  mqttStore.getChargePointConnectedVehiclePvChargingMinSocPhases(
                    modalChargePointId,
                  ) == 1
                    ? 'primary'
                    : ''
                "
                :active="
                  mqttStore.getChargePointConnectedVehiclePvChargingMinSocPhases(
                    modalChargePointId,
                  ) == 1
                "
                @click="
                  setChargePointConnectedVehiclePvChargingMinSocPhases(
                    modalChargePointId,
                    1,
                  )
                "
              >
                1
              </i-button>
              <i-button
                :color="
                  mqttStore.getChargePointConnectedVehiclePvChargingMinSocPhases(
                    modalChargePointId,
                  ) == 3
                    ? 'primary'
                    : ''
                "
                :active="
                  mqttStore.getChargePointConnectedVehiclePvChargingMinSocPhases(
                    modalChargePointId,
                  ) == 3
                "
                @click="
                  setChargePointConnectedVehiclePvChargingMinSocPhases(
                    modalChargePointId,
                    3,
                  )
                "
              >
                Maximum
              </i-button>
            </i-button-group>
          </i-form-group>
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
        </i-form>
      </i-tab>
      <i-tab
        v-if="!mqttStore.getSimpleChargePointView"
        name="tab-eco-charging"
      >
        <i-form>
          <i-form-group>
            <i-form-label>Minimaler Dauerstrom unter Preisgrenze</i-form-label>
            <extended-number-input
              unit="A"
              :min="6"
              :max="32"
              :model-value="
                mqttStore.getChargePointConnectedVehicleEcoChargingCurrent(
                  modalChargePointId,
                )
              "
              @update:model-value="
                setChargePointConnectedVehicleEcoChargingCurrent(
                  modalChargePointId,
                  $event,
                )
              "
            />
          </i-form-group>
          <i-form-group>
            <i-form-label>Anzahl Phasen</i-form-label>
            <i-button-group block>
              <i-button
                :color="
                  mqttStore.getChargePointConnectedVehicleEcoChargingPhases(
                    modalChargePointId,
                  ) == 1
                    ? 'primary'
                    : ''
                "
                :active="
                  mqttStore.getChargePointConnectedVehicleEcoChargingPhases(
                    modalChargePointId,
                  ) == 1
                "
                @click="
                  setChargePointConnectedVehicleEcoChargingPhases(
                    modalChargePointId,
                    1,
                  )
                "
              >
                1
              </i-button>
              <i-button
                :color="
                  mqttStore.getChargePointConnectedVehicleEcoChargingPhases(
                    modalChargePointId,
                  ) == 3
                    ? 'primary'
                    : ''
                "
                :active="
                  mqttStore.getChargePointConnectedVehicleEcoChargingPhases(
                    modalChargePointId,
                  ) == 3
                "
                @click="
                  setChargePointConnectedVehicleEcoChargingPhases(
                    modalChargePointId,
                    3,
                  )
                "
              >
                Maximum
              </i-button>
              <i-button
                :color="
                  mqttStore.getChargePointConnectedVehicleEcoChargingPhases(
                    modalChargePointId,
                  ) == 0
                    ? 'primary'
                    : ''
                "
                :active="
                  mqttStore.getChargePointConnectedVehicleEcoChargingPhases(
                    modalChargePointId,
                  ) == 0
                "
                @click="
                  setChargePointConnectedVehicleEcoChargingPhases(
                    modalChargePointId,
                    0,
                  )
                "
              >
                Automatik
              </i-button>
            </i-button-group>
          </i-form-group>
          <i-form-group>
            <i-form-label>Begrenzung</i-form-label>
            <i-button-group block>
              <i-button
                :color="
                  mqttStore.getChargePointConnectedVehicleEcoChargingLimit(
                    modalChargePointId,
                  ).selected == 'none'
                    ? 'primary'
                    : ''
                "
                :active="
                  mqttStore.getChargePointConnectedVehicleEcoChargingLimit(
                    modalChargePointId,
                  ).selected == 'none'
                "
                @click="
                  setChargePointConnectedVehicleEcoChargingLimit(
                    modalChargePointId,
                    'none',
                  )
                "
              >
                Aus
              </i-button>
              <i-button
                :color="
                  mqttStore.getChargePointConnectedVehicleEcoChargingLimit(
                    modalChargePointId,
                  ).selected == 'soc'
                    ? 'primary'
                    : ''
                "
                :active="
                  mqttStore.getChargePointConnectedVehicleEcoChargingLimit(
                    modalChargePointId,
                  ).selected == 'soc'
                "
                @click="
                  setChargePointConnectedVehicleEcoChargingLimit(
                    modalChargePointId,
                    'soc',
                  )
                "
              >
                EV-SoC
              </i-button>
              <i-button
                :color="
                  mqttStore.getChargePointConnectedVehicleEcoChargingLimit(
                    modalChargePointId,
                  ).selected == 'amount'
                    ? 'primary'
                    : ''
                "
                :active="
                  mqttStore.getChargePointConnectedVehicleEcoChargingLimit(
                    modalChargePointId,
                  ).selected == 'amount'
                "
                @click="
                  setChargePointConnectedVehicleEcoChargingLimit(
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
              mqttStore.getChargePointConnectedVehicleEcoChargingLimit(
                modalChargePointId,
              ).selected == 'soc'
            "
          >
            <i-form-label>SoC-Limit für das Fahrzeug</i-form-label>
            <extended-number-input
              unit="%"
              :min="5"
              :max="100"
              :step="5"
              :model-value="
                mqttStore.getChargePointConnectedVehicleEcoChargingLimit(
                  modalChargePointId,
                ).soc
              "
              @update:model-value="
                setChargePointConnectedVehicleEcoChargingLimitSoc(
                  modalChargePointId,
                  $event,
                )
              "
            />
          </i-form-group>
          <i-form-group
            v-if="
              mqttStore.getChargePointConnectedVehicleEcoChargingLimit(
                modalChargePointId,
              ).selected == 'amount'
            "
          >
            <i-form-label>Energie-Limit</i-form-label>
            <extended-number-input
              unit="kWh"
              :min="1"
              :max="100"
              :model-value="
                mqttStore.getChargePointConnectedVehicleEcoChargingLimit(
                  modalChargePointId,
                ).amount / 1000
              "
              @update:model-value="
                setChargePointConnectedVehicleEcoChargingLimitAmount(
                  modalChargePointId,
                  $event * 1000,
                )
              "
            />
          </i-form-group>
          <i-form-group>
            <i-form-label>Preisgrenze für strompreisbasiertes Laden</i-form-label>
            <extended-number-input
              unit="ct/kWh"
              :min="-80"
              :max="80"
              :step="0.01"
              :precision="2"
              :model-value="
                mqttStore.getChargePointConnectedVehicleEcoChargingMaxPrice(
                  modalChargePointId,
                )
              "
              @update:model-value="
                setChargePointConnectedVehicleEcoChargingMaxPrice(
                  modalChargePointId,
                  $event,
                )
              "
            />
          </i-form-group>
        </i-form>
      </i-tab>
      <i-tab
        v-if="!mqttStore.getSimpleChargePointView"
        name="tab-scheduled-charging"
      >
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
            <font-awesome-icon
              fixed-width
              :icon="['fas', 'fa-info-circle']"
            />
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
                  <font-awesome-icon
                    fixed-width
                    :icon="['fas', 'clock']"
                  />
                  {{ plan.time }}
                  <span v-if="plan.limit.selected == 'soc'">
                    <font-awesome-icon
                      fixed-width
                      :icon="['fas', 'car-battery']"
                    />
                    {{ plan.limit.soc_scheduled }}&nbsp;%
                  </span>
                  <span v-if="plan.limit.selected == 'amount'">
                    <font-awesome-icon
                      fixed-width
                      :icon="['fas', 'bolt']"
                    />
                    {{ plan.limit.amount / 1000 }}&nbsp;kWh
                  </span>
                  <span v-if="plan.et_active">
                    <font-awesome-icon
                      fixed-width
                      :icon="['fas', 'coins']"
                    />
                  </span>
                </i-button>
              </i-row>
            </i-container>
          </i-form-group>
        </i-form>
      </i-tab>
      <i-tab
        v-if="!mqttStore.getSimpleChargePointView"
        name="tab-time-charging"
      >
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
                    <font-awesome-icon
                      fixed-width
                      :icon="['fas', 'clock']"
                    />
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
        </i-form>
      </i-tab>
    </i-tabs>
  </i-modal>
  <!-- end charge point settings modal-->
  <!-- manual soc input -->
  <manual-soc-input
    v-model="modalManualSocInputVisible"
    :vehicle-id="modalVehicleId"
  />
  <!-- end manual soc input -->
</template>

<style scoped>
.charge-points-card-wrapper {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(36rem, 1fr));
  grid-gap: var(--spacing);
}

.large-button {
  height: 3.5rem;
  font-size: 1.5rem;
  padding: 0.75rem 1.5rem;
}

:deep(.toggle .toggle-label::before) {
  border-color: var(--color--dark-45);
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
