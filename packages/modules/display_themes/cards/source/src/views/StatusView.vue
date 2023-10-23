<script>
import { useMqttStore } from "@/stores/mqtt.js";

export default {
  name: "StatusView",
  props: {
    changesLocked: { required: false, type: Boolean, default: false },
  },
  data() {
    return {
      mqttStore: useMqttStore(),
    };
  },
  methods: {
    reloadDisplay() {
      console.debug("reload requested");
      location.reload();
    },
  },
};
</script>

<template>
  <i-container>
    <i-form>
      <i-row>
        <i-column>
          <i-form-group>
            <i-form-label>
              IP-Adresse
            </i-form-label>
            <i-input
              id="input_system_ip"
              plaintext
              :model-value="mqttStore.getSystemIp"
            />
            <i-form-label>
              Systemzeit
            </i-form-label>
            <i-input
              id="input_system_time"
              plaintext
              :model-value="mqttStore.getSystemTime"
            />
            <i-form-label>
              Version
            </i-form-label>
            <i-input
              id="input_system_version"
              plaintext
              :model-value="mqttStore.getSystemVersion"
            />
            <i-form-label>
              Installierte Version (Details)
            </i-form-label>
            <i-input
              id="input_system_branch"
              plaintext
              :model-value="mqttStore.getSystemCurrentCommit"
            />
            <i-form-label>
              Entwicklungszweig
            </i-form-label>
            <i-input
              id="input_system_branch"
              plaintext
              :model-value="mqttStore.getSystemBranch"
            />
          </i-form-group>
        </i-column>
      </i-row>
      <i-row class="_margin-top:5">
        <i-column>
          <i-form-group v-if="!changesLocked">
            <i-button color="danger" @click="reloadDisplay()">Display neu laden</i-button>
          </i-form-group>
        </i-column>
      </i-row>
    </i-form>
  </i-container>
</template>

<style scoped></style>
