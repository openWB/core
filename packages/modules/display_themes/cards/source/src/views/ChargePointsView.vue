<script>
import { useMqttStore } from "@/stores/mqtt.js";
import ChargePointCard from "@/components/ChargePoints/ChargePointCard.vue";
import SimpleChargePointCard from "@/components/ChargePoints/SimpleChargePointCard.vue";
import ExtendedNumberInput from "@/components/ExtendedNumberInput.vue";
import ManualSocInput from "@/components/ChargePoints/ManualSocInput.vue";
import ChargeModeModal from "../components/ChargePoints/ChargeModeModal.vue";
import VehicleSelectModal from "../components/ChargePoints/VehicleSelectModal.vue";
import ElectricityTariffChart from "../components/ElectricityTariffChart.vue";

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
    ChargeModeModal,
    VehicleSelectModal,
    FontAwesomeIcon,
    ElectricityTariffChart,
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
    };
  },
  computed: {
    timeChargingEnabled() {
      return (chargePointId) => {
        return this.mqttStore.getChargePointConnectedVehicleTimeChargingActive(
          chargePointId,
        ) === true;
      };
    }
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
    updateChargePointChargeTemplate(chargePointId, newValue, objectPath = undefined) {
      const chargeTemplate = this.mqttStore.updateState(
        `openWB/chargepoint/${chargePointId}/set/charge_template`,
        newValue,
        objectPath,
      );
      this.$root.sendTopicToBroker(
        `openWB/chargepoint/${chargePointId}/set/charge_template`,
        chargeTemplate,
      );
    },
    setChargePointConnectedVehicleChargeMode(id, event) {
      if (
        event.id != this.mqttStore.getChargePointConnectedVehicleChargeMode(id)
      ) {
        this.updateChargePointChargeTemplate(id, event, "chargemode.selected");
      }
    },
    setChargePointConnectedVehiclePriority(id, event) {
      if (event != this.mqttStore.getChargePointConnectedVehiclePriority(id)) {
        this.updateChargePointChargeTemplate(id, event, "prio");
      }
    },
    setChargePointConnectedVehicleTimeChargingActive(id, event) {
      if (
        event !=
        this.mqttStore.getChargePointConnectedVehicleTimeChargingActive(id)
      ) {
        this.updateChargePointChargeTemplate(id, event, "time_charging.active");
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
        this.updateChargePointChargeTemplate(id, event, "chargemode.instant_charging.current");
      }
    },
    setChargePointConnectedVehicleInstantChargingPhases(id, event) {
      if (
        event &&
        event !=
          this.mqttStore.getChargePointConnectedVehicleInstantChargingPhases(id)
      ) {
        this.updateChargePointChargeTemplate(id, event, "chargemode.instant_charging.phases_to_use");
      }
    },
    setChargePointConnectedVehicleInstantChargingLimit(id, event) {
      if (
        event &&
        event !=
          this.mqttStore.getChargePointConnectedVehicleInstantChargingLimit(id)
            .selected
      ) {
        this.updateChargePointChargeTemplate(id, event, "chargemode.instant_charging.limit.selected");
      }
    },
    setChargePointConnectedVehicleInstantChargingLimitSoc(id, event) {
      if (
        event &&
        event !=
          this.mqttStore.getChargePointConnectedVehicleInstantChargingLimit(id)
            .soc
      ) {
        this.updateChargePointChargeTemplate(id, parseInt(event), "chargemode.instant_charging.limit.soc");
      }
    },
    setChargePointConnectedVehicleInstantChargingLimitAmount(id, event) {
      if (
        event &&
        event !=
          this.mqttStore.getChargePointConnectedVehicleInstantChargingLimit(id)
            .amount
      ) {
        this.updateChargePointChargeTemplate(id, event, "chargemode.instant_charging.limit.amount");
      }
    },
    setChargePointConnectedVehiclePvChargingFeedInLimit(id, event) {
      if (
        event !=
        this.mqttStore.getChargePointConnectedVehiclePvChargingFeedInLimit(id)
      ) {
        this.updateChargePointChargeTemplate(id, event, "chargemode.pv_charging.feed_in_limit");
      }
    },
    setChargePointConnectedVehiclePvChargingMinCurrent(id, event) {
      let previous_value =
        this.mqttStore.getChargePointConnectedVehiclePvChargingMinCurrent(id);
      let new_value = parseInt(event);
      if (new_value != previous_value && !isNaN(new_value)) {
        this.updateChargePointChargeTemplate(id, new_value, "chargemode.pv_charging.min_current");
      }
    },
    setChargePointConnectedVehiclePvChargingPhases(id, selected_phases) {
      if (
        selected_phases !== undefined &&
        selected_phases !=
          this.mqttStore.getChargePointConnectedVehiclePvChargingPhases(id)
      ) {
        this.updateChargePointChargeTemplate(id, selected_phases, "chargemode.pv_charging.phases_to_use");
      }
    },
    setChargePointConnectedVehiclePvChargingLimit(id, selected_limit) {
      if (
        selected_limit &&
        selected_limit !=
          this.mqttStore.getChargePointConnectedVehiclePvChargingLimit(id)
            .selected
      ) {
        this.updateChargePointChargeTemplate(id, selected_limit, "chargemode.pv_charging.limit.selected");
      }
    },
    setChargePointConnectedVehiclePvChargingLimitSoc(id, soc_limit) {
      if (
        soc_limit &&
        soc_limit !=
          this.mqttStore.getChargePointConnectedVehiclePvChargingLimit(id)
            .soc
      ) {
        this.updateChargePointChargeTemplate(id, parseInt(soc_limit), "chargemode.pv_charging.limit.soc");
      }
    },
    setChargePointConnectedVehiclePvChargingLimitAmount(id, amount_limit) {
      if (
        amount_limit &&
        amount_limit !=
          this.mqttStore.getChargePointConnectedVehiclePvChargingLimit(id)
            .amount
      ) {
        this.updateChargePointChargeTemplate(id, amount_limit, "chargemode.pv_charging.limit.amount");
      }
    },
    setChargePointConnectedVehiclePvChargingMinSoc(id, soc) {
      let previous_value =
        this.mqttStore.getChargePointConnectedVehiclePvChargingMinSoc(id);
      let new_value = parseInt(soc);
      if (new_value != previous_value && !isNaN(new_value)) {
        this.updateChargePointChargeTemplate(id, new_value, "chargemode.pv_charging.min_soc");
      }
    },
    setChargePointConnectedVehiclePvChargingMinSocCurrent(id, event) {
      let previous_value =
        this.mqttStore.getChargePointConnectedVehiclePvChargingMinSocCurrent(
          id,
        );
      let new_value = parseInt(event);
      if (new_value != previous_value && !isNaN(new_value)) {
        this.updateChargePointChargeTemplate(id, new_value, "chargemode.pv_charging.min_soc_current");
      }
    },
    setChargePointConnectedVehiclePvChargingMinSocPhases(id, selected_phases) {
      if (
        selected_phases &&
        selected_phases !=
          this.mqttStore.getChargePointConnectedVehiclePvChargingMinSocPhases(id)
      ) {
        this.updateChargePointChargeTemplate(id, selected_phases, "chargemode.pv_charging.phases_to_use_min_soc");
      }
    },
    setChargePointConnectedVehicleEcoChargingCurrent(id, event) {
      let previous_value =
        this.mqttStore.getChargePointConnectedVehicleEcoChargingCurrent(id);
      let new_value = parseInt(event);
      if (new_value != previous_value && !isNaN(new_value)) {
        this.updateChargePointChargeTemplate(id, new_value, "chargemode.eco_charging.current");
      }
    },
    setChargePointConnectedVehicleEcoChargingPhases(id, selected_phases) {
      if (
        selected_phases !== undefined &&
        selected_phases !=
          this.mqttStore.getChargePointConnectedVehicleEcoChargingPhases(id)
      ) {
        this.updateChargePointChargeTemplate(id, selected_phases, "chargemode.eco_charging.phases_to_use");
      }
    },
    setChargePointConnectedVehicleEcoChargingLimit(id, selected_limit) {
      if (
        selected_limit &&
        selected_limit !=
          this.mqttStore.getChargePointConnectedVehicleEcoChargingLimit(id)
            .selected
      ) {
        this.updateChargePointChargeTemplate(id, selected_limit, "chargemode.eco_charging.limit.selected");
      }
    },
    setChargePointConnectedVehicleEcoChargingLimitSoc(id, soc_limit) {
      if (
        soc_limit &&
        soc_limit !=
          this.mqttStore.getChargePointConnectedVehicleEcoChargingLimit(id)
            .soc
      ) {
        this.updateChargePointChargeTemplate(id, parseInt(soc_limit), "chargemode.eco_charging.limit.soc");
      }
    },
    setChargePointConnectedVehicleEcoChargingLimitAmount(id, amount_limit) {
      if (
        amount_limit &&
        amount_limit !=
          this.mqttStore.getChargePointConnectedVehicleEcoChargingLimit(id)
            .amount
      ) {
        this.updateChargePointChargeTemplate(id, amount_limit, "chargemode.eco_charging.limit.amount");
      }
    },
    setChargePointConnectedVehicleEcoChargingMaxPrice(id, event) {
      let previous_value =
        this.mqttStore.getChargePointConnectedVehicleEcoChargingMaxPrice(id);
      let new_value = parseFloat(event);
      if (new_value != previous_value && !isNaN(new_value)) {
        this.updateChargePointChargeTemplate(id, parseFloat((new_value / 100000).toFixed(7)), "chargemode.eco_charging.max_price");
      }
    },
    setChargePointConnectedVehicleScheduledChargingPlanActive(
      plan_key,
      active,
    ) {
      const plan = this.mqttStore.updateState(
        `${plan_key}`,
        active,
        "active",
      );
      this.$root.sendTopicToBroker(`${plan_key}`, plan);
    },
    setChargePointConnectedVehicleTimeChargingPlanActive(plan_key, active) {
      const plan = this.mqttStore.updateState(
        `${plan_key}`,
        active,
        "active",
      );
      this.$root.sendTopicToBroker(`${plan_key}`, plan);
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
  <charge-mode-modal
    v-model="modalChargeModeSettingVisible"
    :charge-point-id="modalChargePointId"
  />
  <!-- vehicle only -->
  <vehicle-select-modal
    v-model="modalVehicleSelectVisible"
    :charge-point-id="modalChargePointId"
  />
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
          <i-form-group v-if="mqttStore.getEtConfigured">
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
            <ElectricityTariffChart
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
                  <div class="plan-name">
                    {{ plan.name }}
                  </div>
                  <div class="plan-details">
                    <div v-if="plan.frequency.selected == 'once'">
                      <font-awesome-icon
                        :icon="['fas', 'calendar-day']"
                      />
                      {{ mqttStore.formatDate(plan.frequency.once) }}
                    </div>
                    <div v-if="plan.frequency.selected == 'daily'">
                      <font-awesome-icon
                        :icon="['fas', 'calendar-week']"
                      />
                      täglich
                    </div>
                    <div v-if="plan.frequency.selected == 'weekly'">
                      <font-awesome-icon
                        :icon="['fas', 'calendar-alt']"
                      />
                      {{
                        mqttStore.formatWeeklyScheduleDays(plan.frequency.weekly)
                      }}
                    </div>
                    <div>
                      <font-awesome-icon
                        :icon="['fas', 'clock']"
                      />
                      {{ plan.time }}
                    </div>
                    <div v-if="plan.limit.selected == 'soc'">
                      <font-awesome-icon
                        :icon="['fas', 'car-battery']"
                      />
                      {{ plan.limit.soc_scheduled }}&nbsp;%
                    </div>
                    <div v-if="plan.limit.selected == 'amount'">
                      <font-awesome-icon
                        :icon="['fas', 'bolt']"
                      />
                      {{ plan.limit.amount / 1000 }}&nbsp;kWh
                    </div>
                    <div v-if="plan.et_active">
                      <font-awesome-icon
                        :icon="['fas', 'coins']"
                      />
                    </div>
                  </div>
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
          <i-form-group class="_margin-bottom:2">
            <i-form-label>Zeitladen aktivieren</i-form-label>
            <i-button-group block>
              <i-button
                :color="
                  !timeChargingEnabled(modalChargePointId)
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
                  timeChargingEnabled(modalChargePointId)
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
                    <div class="plan-name">
                      {{ plan.name }}
                    </div>
                    <div class="plan-details">
                      <div v-if="plan.frequency.selected == 'once'">
                        <font-awesome-icon
                          :icon="['fas', 'calendar-day']"
                        />
                        {{ mqttStore.formatDateRange(plan.frequency.once) }}
                      </div>
                      <div v-if="plan.frequency.selected == 'daily'">
                        <font-awesome-icon
                          :icon="['fas', 'calendar-week']"
                        />
                        täglich
                      </div>
                      <div v-if="plan.frequency.selected == 'weekly'">
                        <font-awesome-icon
                          :icon="['fas', 'calendar-alt']"
                        />
                        {{
                          mqttStore.formatWeeklyScheduleDays(
                            plan.frequency.weekly,
                          )
                        }}
                      </div>
                      <div>
                        <font-awesome-icon
                          :icon="['fas', 'clock']"
                        />
                        {{ plan.time.join("-") }}
                      </div>
                      <div v-if="plan.limit.selected == 'soc'">
                        <font-awesome-icon
                          :icon="['fas', 'car-battery']"
                        />
                        {{ plan.limit.soc }}&nbsp;%
                      </div>
                      <div v-if="plan.limit.selected == 'amount'">
                        <font-awesome-icon
                          :icon="['fas', 'bolt']"
                        />
                        {{ plan.limit.amount / 1000 }}&nbsp;kWh
                      </div>
                    </div>
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
</template>

<style scoped>
.charge-points-card-wrapper {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(36rem, 1fr));
  grid-gap: var(--spacing);
}

:deep(.toggle .toggle-label::before) {
  border-color: var(--color--dark-45);
}

:deep(.tab) {
  min-height: 72vh;
  max-height: 72vh;
  overflow-y: scroll;
}

:deep(.input-prepend),
:deep(.input-append) {
  min-width: 3em;
}

.plan-name {
  font-weight: bold;
}

.plan-details {
  display: flex;
  flex-wrap: nowrap;
  justify-content: center;
}

.plan-details > div:not(:last-child) {
  margin-right: 0.5em;
}
</style>
