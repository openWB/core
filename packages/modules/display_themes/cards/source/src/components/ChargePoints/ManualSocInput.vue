<script>
import ExtendedNumberInput from "@/components/ExtendedNumberInput.vue";
import NumberPad from "../NumberPad.vue";

import { useMqttStore } from "@/stores/mqtt.js";

export default {
  name: "ManualSocInput",
  props: {
    modelValue: { required: true, type: Boolean, default: false },
    vehicleId: { required: true, type: Number, default: 0 },
  },
  data() {
    return {
      mqttStore: useMqttStore(),
      newSoc: 0,
    };
  },
  components: {
    ExtendedNumberInput,
    NumberPad,
  },
  emits: ["update:modelValue"],
  methods: {
    enter(digit) {
      let tempSoc = this.newSoc * 10 + parseInt(digit);
      if (tempSoc >= 0 && tempSoc <= 100) {
        this.newSoc = tempSoc;
      }
    },
    removeDigit() {
      this.newSoc = Math.trunc(this.newSoc / 10);
    },
    clear() {
      this.newSoc = 0;
    },
    close() {
      this.$emit("update:modelValue", false);
      this.newSoc = 0;
    },
    updateManualSoc() {
      this.$root.sendTopicToBroker(
        `openWB/vehicle/${this.vehicleId}/soc_module/calculated_soc_state/manual_soc`,
        this.newSoc,
      );
      this.close();
    },
  },
};
</script>

<template>
  <Teleport to="body">
    <i-modal
      :modelValue="modelValue"
      @update:modelValue="$emit('update:modelValue', $event)"
      size="sm"
    >
      <template #header>
        SoC für Fahrzeug "{{ mqttStore.getVehicleName(vehicleId) }}"
      </template>
      <i-container>
        <i-row center class="_padding-bottom:1">
          <i-column>
            <extended-number-input
              v-model="newSoc"
              unit="%"
              :min="0"
              :max="100"
              :step="1"
              size="lg"
              class="_text-align:center"
            />
          </i-column>
        </i-row>
        <NumberPad
          @key:digit="enter($event)"
          @key:clear="clear()"
          @key:delete="removeDigit()"
        />
      </i-container>
      <template #footer>
        <i-container>
          <i-row>
            <!-- charge point data on left side -->
            <i-column>
              <i-button color="danger" @click="close()"> Zurück </i-button>
            </i-column>
            <i-column class="_text-align:right">
              <i-button color="success" @click="updateManualSoc()">
                OK
              </i-button>
            </i-column>
          </i-row>
        </i-container>
      </template>
    </i-modal>
  </Teleport>
</template>

<style scoped></style>
