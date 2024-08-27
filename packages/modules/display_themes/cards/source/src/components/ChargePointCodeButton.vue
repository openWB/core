<script>
/* fontawesome */
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { faCalculator as fasCalculator } from "@fortawesome/free-solid-svg-icons";
/* add icons to the library */
library.add(fasCalculator);

import { useMqttStore } from "@/stores/mqtt.js";
import CodeInputModal from "./CodeInputModal.vue";

export default {
  name: "ChargePointCodeButton",
  components: {
    FontAwesomeIcon,
    CodeInputModal,
  },
  props: {
    chargePointId: { type: Number, required: true },
  },
  data() {
    return {
      mqttStore: useMqttStore(),
      modalIdTagEntryVisible: false,
      modalIdTagEntryColor: "warning",
      code: "",
    };
  },
  computed: {
    tagState() {
      return this.mqttStore.getChargepointTagState(this.chargePointId);
    },
    tagButtonColor() {
      switch (this.tagState) {
        case 2:
          return "success";
        case 1:
          return "warning";
        default:
          return "";
      }
    },
    tagClass() {
      switch (this.tagState) {
        case 2:
          return "_color:success-80";
        case 1:
          return "_color:warning-80";
        default:
          return "";
      }
    },
  },
  methods: {
    toggleIdTagModal() {
      this.modalIdTagEntryVisible = !this.modalIdTagEntryVisible;
    },
    sendIdTag(event) {
      this.$root.sendTopicToBroker(
        `openWB/chargepoint/${this.chargePointId}/get/rfid`,
        event,
      );
      this.modalIdTagEntryVisible = false;
    },
  },
};
</script>

<template>
  <i-button
    class="_margin-right:1"
    size="lg"
    :color="tagButtonColor"
    :disabled="tagState == 2"
    @click="toggleIdTagModal()"
  >
    <FontAwesomeIcon
      fixed-width
      :icon="['fas', 'fa-calculator']"
      :class="tagClass"
    />
  </i-button>
  <!-- modals -->
  <CodeInputModal
    ref="lockInput"
    v-model="modalIdTagEntryVisible"
    :min-length="4"
    :max-length="20"
    @update:input-value="sendIdTag"
  >
    <template #header>
      Bitte einen ID-Tag eingeben.
    </template>
  </CodeInputModal>
</template>

<style scoped></style>
