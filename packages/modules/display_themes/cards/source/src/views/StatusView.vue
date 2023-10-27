<script>
import { useMqttStore } from "@/stores/mqtt.js";
import ReloadButton from "@/components/Status/ReloadButton.vue";
import RebootButton from "@/components/Status/RebootButton.vue";
import ShutdownButton from "@/components/Status/ShutdownButton.vue";
import DashBoardCard from "@/components/DashBoardCard.vue";

export default {
  name: "StatusView",
  props: {
    changesLocked: { required: false, type: Boolean, default: false },
  },
  components: {
    ReloadButton,
    RebootButton,
    ShutdownButton,
    DashBoardCard,
  },
  data() {
    return {
      mqttStore: useMqttStore(),
    };
  },
};
</script>

<template>
  <div class="status-card-wrapper">
  <dash-board-card
    color="primary"
  >
    <template #headerLeft>
      Status
    </template>
  <i-container>
    <i-form>
      <i-row>
        <i-column>
          <i-form-group>
            <i-row class="_margin-top:2">
              <i-column class="label-column">
                <i-form-label> IP-Adresse </i-form-label>
              </i-column>
              <i-column class="_padding-left:0">
                <i-input
                  id="input_system_ip"
                  plaintext
                  :model-value="mqttStore.getSystemIp"
                />
              </i-column>
            </i-row >
            <i-row class="_margin-top:1">
              <i-column class="label-column">
                <i-form-label> Systemzeit </i-form-label>
              </i-column>
              <i-column class="_padding-left:0">
                <i-input
                  id="input_system_time"
                  plaintext
                  :model-value="mqttStore.getSystemTime"
                />
              </i-column>
            </i-row>       
            <i-row class="_margin-top:1">
              <i-column class="label-column">
                <i-form-label> Version </i-form-label>
              </i-column>
              <i-column class="_padding-left:0">
                <i-input
                  id="input_system_version"
                  plaintext
                  :model-value="mqttStore.getSystemVersion"
                />
              </i-column>
            </i-row>
            <i-row class="_margin-top:1">
              <i-column class="label-column">
                <i-form-label> Installierte Version (Details) </i-form-label>
              </i-column>
              <i-column class="_padding-left:0">
                <i-input
                  id="input_system_commit"
                  plaintext
                  :model-value="mqttStore.getSystemCurrentCommit"
                />
              </i-column>
            </i-row>
            <i-row class="_margin-top:1">
              <i-column class="label-column">
                <i-form-label> Entwicklungszweig </i-form-label>
              </i-column>
              <i-column class="_padding-left:0">
                <i-input
                  id="input_system_branch"
                  plaintext
                  :model-value="mqttStore.getSystemBranch"
                />
              </i-column>
            </i-row>
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
  </dash-board-card>
  </div>
</template>

<style scoped>
.label-column.column{
  max-width: 230px; 
}

.status-card-wrapper {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(36rem, 1fr));
  grid-gap: var(--spacing);
}
</style>

