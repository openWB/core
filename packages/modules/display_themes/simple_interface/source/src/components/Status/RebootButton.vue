<script>
/* fontawesome */
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { faUndo as fasUndo } from "@fortawesome/free-solid-svg-icons";
/* add icons to the library */
library.add(fasUndo);

import { useMqttStore } from "@/stores/mqtt.js";

export default {
  name: "RebootButton",
  props: {},
  data() {
    return {
      mqttStore: useMqttStore(),
      showModal: false,
    };
  },
  components: {
    FontAwesomeIcon,
  },
  methods: {
    /**
     * toggle visibility of our modal
     */
    toggleModal() {
      this.showModal = !this.showModal;
    },
    /**
     * called when our modal was canceled
     */
    cancel() {
      this.toggleModal();
    },
    /**
     * called when our modal was confirmed
     * system reboot is requested by command
     */
    confirm() {
      console.log("reboot requested");
      this.$root.sendSystemCommand("systemReboot");
    },
  },
};
</script>

<template>
  <i-button color="warning" @click="toggleModal()">
    openWB neu starten
    <FontAwesomeIcon fixed-width :icon="['fas', 'fa-undo']" />
    <Teleport to="body">
      <i-modal v-model="showModal" size="sm">
        <template #header> openWB neu starten... </template>
        <i-container>
          Möchten Sie diese openWB wirklich neu starten?
        </i-container>
        <template #footer>
          <i-container>
            <i-row>
              <i-column class="_text-align:right">
                <i-button color="success" @click="cancel()"> Zurück </i-button>
              </i-column>
              <i-column>
                <i-button color="danger" @click="confirm()">Neustart</i-button>
              </i-column>
            </i-row>
          </i-container>
        </template>
      </i-modal>
    </Teleport>
  </i-button>
</template>

<style scoped></style>
