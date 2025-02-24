<script>
import { useMqttStore } from "@/stores/mqtt.js";

export default {
  name: "ChargeModeModal",
  props: {
    modelValue: { required: true, type: Boolean, default: false },
    chargePointId: {
      type: Number,
      required: true,
    },
  },
  emits: ["update:modelValue"],
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
    setChargePointConnectedVehicleChargeMode(modeId) {
      if (modeId != this.mqttStore.getChargePointConnectedVehicleChargeMode(this.chargePointId)) {
        this.updateChargePointChargeTemplate(this.chargePointId, modeId, "chargemode.selected");
      }
    },
    setChargePointConnectedVehiclePriority(priority) {
      if (priority != this.mqttStore.getChargePointConnectedVehiclePriority(this.chargePointId)) {
        this.updateChargePointChargeTemplate(this.chargePointId, priority, "prio");
      }
    },
  },
}
</script>

<template>
  <!-- charge mode only -->
  <i-modal
    :model-value="modelValue"
    size="lg"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <template #header>
      XX Lademodus für "{{
        mqttStore.getChargePointConnectedVehicleName(chargePointId)
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
                chargePointId,
              ) != undefined &&
                mode.id ==
                mqttStore.getChargePointConnectedVehicleChargeMode(
                  chargePointId,
                ).mode
            "
            @click="
              setChargePointConnectedVehicleChargeMode(mode.id)
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
                chargePointId,
              ) !== true
                ? 'danger'
                : ''
            "
            @click="
              setChargePointConnectedVehiclePriority(false)
            "
          >
            Nein
          </i-button>
          <i-button
            :color="
              mqttStore.getChargePointConnectedVehiclePriority(
                chargePointId,
              ) === true
                ? 'success'
                : ''
            "
            @click="
              setChargePointConnectedVehiclePriority(true)
            "
          >
            Ja
          </i-button>
        </i-button-group>
      </i-form-group>
    </i-form>
  </i-modal>
  <!-- end charge mode only-->
</template>

<style scoped>
.large-button {
  height: 3.5rem;
  font-size: 1.5rem;
  padding: 0.75rem 1.5rem;
}
</style>
