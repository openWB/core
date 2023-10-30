<script>
import { useMqttStore } from "@/stores/mqtt.js";
import ReloadButton from "@/components/Status/ReloadButton.vue";
import RebootButton from "@/components/Status/RebootButton.vue";
import ShutdownButton from "@/components/Status/ShutdownButton.vue";

export default {
  name: "StatusView",
  props: {
    changesLocked: { required: false, type: Boolean, default: false },
  },
  components: {
    ReloadButton,
    RebootButton,
    ShutdownButton,
  },
  data() {
    return {
      mqttStore: useMqttStore(),
    };
  },
};
</script>

<template>
  <i-container>
    <i-form>
      <i-row>
        <i-column>
          <i-form-group>
            <i-form-label> IP-Adresse </i-form-label>
            <i-input
              id="input_system_ip"
              plaintext
              :model-value="mqttStore.getSystemIp"
            />
            <i-form-label> Systemzeit </i-form-label>
            <i-input
              id="input_system_time"
              plaintext
              :model-value="mqttStore.getSystemTime"
            />
            <i-form-label> Version </i-form-label>
            <i-input
              id="input_system_version"
              plaintext
              :model-value="mqttStore.getSystemVersion"
            />
            <i-form-label> Installierte Version (Details) </i-form-label>
            <i-input
              id="input_system_commit"
              plaintext
              :model-value="mqttStore.getSystemCurrentCommit"
            />
            <i-form-label> Entwicklungszweig </i-form-label>
            <i-input
              id="input_system_branch"
              plaintext
              :model-value="mqttStore.getSystemBranch"
            />
          </i-form-group>
        </i-column>
      </i-row>
      <i-row v-if="!changesLocked" class="_margin-top:5" between>
        <i-column>
          <reload-button block />
        </i-column>
      </i-row>
      <i-row v-if="!changesLocked" class="_margin-top:2" between>
        <i-column>
          <reboot-button block />
        </i-column>
        <i-column>
          <shutdown-button block />
        </i-column>
      </i-row>
    </i-form>
  </i-container>
</template>

<style scoped></style>
