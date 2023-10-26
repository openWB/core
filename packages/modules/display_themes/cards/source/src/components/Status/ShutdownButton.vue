<script>
/* fontawesome */
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { faPowerOff as fasPowerOff } from "@fortawesome/free-solid-svg-icons";
/* add icons to the library */
library.add(fasPowerOff);

import { useMqttStore } from "@/stores/mqtt.js";

export default {
  name: "ShutdownButton",
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
     * system shutdown is requested by command
     */
    confirm() {
      console.log("shutdown requested");
      this.$root.sendSystemCommand("systemShutdown");
    },
  },
};
</script>

<template>
  <i-button color="danger" @click="toggleModal()">
    openWB ausschalten
    <FontAwesomeIcon fixed-width :icon="['fas', 'fa-power-off']" />
    <Teleport to="body">
      <i-modal v-model="showModal" size="sm">
        <template #header> openWB ausschalten... </template>
        <i-container>
          Möchten Sie diese openWB wirklich ausschalten?<br />
          Nach dem Ausschalten muss die Ladestation komplett spannungsfrei
          geschaltet werden. Erst beim erneuten Zuschalten der Spannung fährt
          das System wieder hoch.
        </i-container>
        <template #footer>
          <i-container>
            <i-row>
              <i-column class="_text-align:right">
                <i-button color="success" @click="cancel()"> Zurück </i-button>
              </i-column>
              <i-column>
                <i-button color="danger" @click="confirm()"
                  >Ausschalten</i-button
                >
              </i-column>
            </i-row>
          </i-container>
        </template>
      </i-modal>
    </Teleport>
  </i-button>
</template>

<style scoped></style>
