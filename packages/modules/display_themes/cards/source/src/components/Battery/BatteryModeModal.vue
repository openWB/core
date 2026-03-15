<template>
  <i-modal
    :model-value="modelValue"
    size="lg"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <template #header>
      Speicher-Beachtung: Überschuss primär für
    </template>
    <i-form>
      <i-form-group>
        <i-button-group
          block
          vertical
        >
          <i-button
            v-for="mode in batteryModes"
            :key="mode.value"
            size="lg"
            class="large-button"
            outline
            :color="mode.color != 'dark' ? mode.color : 'light'"
            :active="mode.value === mqttStore.getBatteryMode"
            @click="
              setBatteryMode(mode.value)
            "
          >
            {{ mode.label }}
          </i-button>
        </i-button-group>
      </i-form-group>
    </i-form>
  </i-modal>
</template>

<script>
import { useMqttStore } from "@/stores/mqtt.js";
export default {
  name: "BatteryModeModal",
  props: {
    modelValue: { required: true, type: Boolean },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      mqttStore: useMqttStore(),
      batteryModes: [
        {
          value: 'ev_mode',
          label: 'Fahrzeuge',
          color: 'primary',
        },
        {
          value: 'bat_mode',
          label: 'Speicher',
          color: 'primary',
        },
        {
          value: 'min_soc_bat_mode',
          label: 'Mindest-SoC',
          color: 'primary',
        },
      ]
    };
  },
  methods: {
    setBatteryMode(mode) {
      if(mode !== this.mqttStore.getBatteryMode) {
        this.mqttStore.updateState("openWB/general/chargemode_config/pv_charging/bat_mode", mode);
        this.$root.sendTopicToBroker("openWB/general/chargemode_config/pv_charging/bat_mode", mode);
      }
    },
  },
};
</script>
