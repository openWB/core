<script>
import ExtendedNumberInput from "@/components/ExtendedNumberInput.vue";

/* fontawesome */
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import {
  faDeleteLeft as fasDeleteLeft,
  faEraser as fasEraser,
} from "@fortawesome/free-solid-svg-icons";
/* add icons to the library */
library.add(fasDeleteLeft, fasEraser);

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
    FontAwesomeIcon,
  },
  emits: ["update:modelValue"],
  methods: {
    enter(digit) {
      let tempSoc = this.newSoc * 10 + digit;
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
        `openWB/vehicle/${this.vehicleId}/soc_module/configuration/soc_start`,
        this.newSoc
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
        <i-row center class="_padding-bottom:1">
          <i-column class="_flex-grow:0">
            <i-button size="lg" class="numberButton" @click="enter(1)"
              >1</i-button
            >
          </i-column>
          <i-column class="_flex-grow:0">
            <i-button size="lg" class="numberButton" @click="enter(2)"
              >2</i-button
            >
          </i-column>
          <i-column class="_flex-grow:0">
            <i-button size="lg" class="numberButton" @click="enter(3)"
              >3</i-button
            >
          </i-column>
        </i-row>
      </i-container>
      <i-container>
        <i-row center class="_padding-bottom:1">
          <i-column class="_flex-grow:0">
            <i-button size="lg" class="numberButton" @click="enter(4)"
              >4</i-button
            >
          </i-column>
          <i-column class="_flex-grow:0">
            <i-button size="lg" class="numberButton" @click="enter(5)"
              >5</i-button
            >
          </i-column>
          <i-column class="_flex-grow:0">
            <i-button size="lg" class="numberButton" @click="enter(6)"
              >6</i-button
            >
          </i-column>
        </i-row>
      </i-container>
      <i-container>
        <i-row center class="_padding-bottom:1">
          <i-column class="_flex-grow:0">
            <i-button size="lg" class="numberButton" @click="enter(7)"
              >7</i-button
            >
          </i-column>
          <i-column class="_flex-grow:0">
            <i-button size="lg" class="numberButton" @click="enter(8)"
              >8</i-button
            >
          </i-column>
          <i-column class="_flex-grow:0">
            <i-button size="lg" class="numberButton" @click="enter(9)"
              >9</i-button
            >
          </i-column>
        </i-row>
      </i-container>
      <i-container>
        <i-row center class="_padding-bottom:1">
          <i-column class="_flex-grow:0">
            <i-button size="lg" class="numberButton" @click="clear()">
              <FontAwesomeIcon fixed-width :icon="['fas', 'fa-eraser']" />
            </i-button>
          </i-column>
          <i-column class="_flex-grow:0">
            <i-button size="lg" class="numberButton" @click="enter(0)"
              >0</i-button
            >
          </i-column>
          <i-column class="_flex-grow:0">
            <i-button size="lg" class="numberButton" @click="removeDigit()">
              <FontAwesomeIcon fixed-width :icon="['fas', 'fa-delete-left']" />
            </i-button>
          </i-column>
        </i-row>
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

<style scoped>
.numberButton {
  min-width: 3em;
  min-height: 3em;
}
</style>
