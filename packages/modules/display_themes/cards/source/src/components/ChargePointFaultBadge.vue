<script>
import { useMqttStore } from "@/stores/mqtt.js";

/* fontawesome */
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import {
  faCheckCircle as fasCheckCircle,
  faExclamationTriangle as fasExclamationTriangle,
  faTimesCircle as fasTimesCircle,
} from "@fortawesome/free-solid-svg-icons";
/* add icons to the library */
library.add(fasCheckCircle, fasExclamationTriangle, fasTimesCircle);

export default {
  name: "ChargePointFaultBadge",
  components: { FontAwesomeIcon },
  props: {
    chargePointId: { required: true, type: Array },
  },
  data() {
    return {
      mqttStore: useMqttStore(),
    };
  },
  computed: {
    faultState() {
      if (this.chargePointId.length != 1) {
        return 0;
      }
      return this.mqttStore.getChargePointFaultState(this.chargePointId[0]);
    },
    faultIcon() {
      if (this.faultState == 2) {
        return ["fas", "fa-times-circle"];
      }
      if (this.faultState == 1) {
        return ["fas", "fa-exclamation-triangle"];
      }
      return ["fas", "fa-check-circle"];
    },
    faultClass() {
      if (this.faultState == 2) {
        return "_color:danger";
      }
      if (this.faultState == 1) {
        return "_color:warning";
      }
      return "_color:success";
    },
  },
};
</script>

<template>
  <i-badge
    v-if="faultState > 0"
    size="lg"
    class="clickable"
    @click="showFaultModal = true"
  >
    <font-awesome-icon
      fixed-width
      :icon="faultIcon"
      :class="faultClass"
    />
  </i-badge>
</template>

<style scoped>
.wrap {
  white-space: normal;
}
</style>
