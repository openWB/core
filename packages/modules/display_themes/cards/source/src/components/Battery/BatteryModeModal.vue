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
            <i-row>
              <i-column>
                <font-awesome-icon
                  fixed-width
                  :icon="mode.symbol.icon"
                  :rotation="mode.symbol.rotation"
                />
              </i-column>
              <i-column>
                {{ mode.label }}
              </i-column>
            </i-row>
          </i-button>
        </i-button-group>
      </i-form-group>
    </i-form>
  </i-modal>
</template>

<script>
import { useMqttStore } from "@/stores/mqtt.js";

/* fontawesome */
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import {
  faBatteryFull as fasBatteryFull,
  faBatteryHalf as fasBatteryHalf,
  faCar as fasCar
} from "@fortawesome/free-solid-svg-icons";
/* add icons to the library */
library.add(fasBatteryFull, fasBatteryHalf, fasCar);

export default {
  name: "BatteryModeModal",
  components: { FontAwesomeIcon },
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
          symbol: { icon: ['fas', 'fa-car'], rotation: 0 },
        },
        {
          value: 'bat_mode',
          label: 'Speicher',
          color: 'primary',
          symbol: {
            icon: ['fas', 'battery-full'],
            rotation: 270,
          },
        },
        {
          value: 'min_soc_bat_mode',
          label: 'Mindest-SoC',
          color: 'primary',
          symbol: {
            icon: ['fas', 'battery-half'],
            rotation: 270,
          },
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
