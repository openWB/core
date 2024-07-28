<script>
import { useMqttStore } from "@/stores/mqtt.js";

/* fontawesome */
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import {
  faLock as fasLock,
  faLockOpen as fasLockOpen,
} from "@fortawesome/free-solid-svg-icons";
/* add icons to the library */
library.add(fasLock, fasLockOpen);

export default {
  name: "ChargePointLockButton",
  components: { FontAwesomeIcon },
  props: {
    chargePointId: { required: true, type: Number },
    changesLocked: { required: false, type: Boolean, default: false },
  },
  data() {
    return {
      mqttStore: useMqttStore(),
    };
  },
  computed: {
    locked() {
      return this.mqttStore.getChargePointManualLock(this.chargePointId);
    },
    stateIcon() {
      if (this.locked) {
        return ["fas", "fa-lock"];
      }
      return ["fas", "fa-lock-open"];
    },
    stateClass() {
      if (this.locked) {
        return ["_color:danger"];
      }
      return "_color:success";
    },
  },
  methods: {
    toggleChargePointManualLock() {
      if (!this.changesLocked) {
        this.$root.sendTopicToBroker(
          `openWB/chargepoint/${this.chargePointId}/set/manual_lock`,
          !this.mqttStore.getValueBool(
            `openWB/chargepoint/${this.chargePointId}/set/manual_lock`,
          ),
        );
      }
    },
  },
};
</script>

<template>
  <i-button
    size="lg"
    :disabled="changesLocked"
    :outline="changesLocked"
  >
    <font-awesome-icon
      fixed-width
      :icon="stateIcon"
      :class="stateClass"
      @click="toggleChargePointManualLock()"
    />
  </i-button>
</template>
