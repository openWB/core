<script>
import { useMqttStore } from "@/stores/mqtt.js";

/* fontawesome */
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import {
  faPlugCircleXmark as fasPlugCircleXmark,
  faPlugCircleCheck as fasPlugCircleCheck,
  faPlugCircleBolt as fasPlugCircleBolt,
} from "@fortawesome/free-solid-svg-icons";
/* add icons to the library */
library.add(fasPlugCircleXmark, fasPlugCircleCheck, fasPlugCircleBolt);

export default {
  name: "ChargePointStateBadge",
  components: { FontAwesomeIcon },
  props: {
    chargePointId: { required: true, type: Array },
    showEnergyCharged: { required: false, type: Boolean, default: true },
  },
  data() {
    return {
      mqttStore: useMqttStore(),
    };
  },
  computed: {
    plugState() {
      var connected = false;
      this.chargePointId.forEach((id) => {
        connected |= this.mqttStore.getChargePointPlugState(id);
      });
      return connected;
    },
    chargeState() {
      var charging = false;
      this.chargePointId.forEach((id) => {
        charging |= this.mqttStore.getChargePointChargeState(id);
      });
      return charging;
    },
    stateIcon() {
      if (this.plugState) {
        if (this.chargeState) {
          return ["fas", "fa-plug-circle-bolt"];
        }
        return ["fas", "fa-plug-circle-check"];
      }
      return ["fas", "fa-plug-circle-xmark"];
    },
    stateClass() {
      if (this.plugState) {
        if (this.chargeState) {
          return "_color:success";
        }
        return "_color:warning";
      }
      return "_color:gray";
    },
  },
};
</script>

<template>
  <i-badge size="lg">
    <font-awesome-icon
      fixed-width
      :icon="stateIcon"
      :class="stateClass"
    />
    <span
      v-if="plugState && showEnergyCharged"
      class="_padding-left:1"
    >
      {{ mqttStore.getChargePointImportedSincePlugged(chargePointId).energy }} /
      {{ mqttStore.getChargePointImportedSincePlugged(chargePointId).range }}
    </span>
  </i-badge>
</template>
