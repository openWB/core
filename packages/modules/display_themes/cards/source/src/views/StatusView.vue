<script>
import { useMqttStore } from "@/stores/mqtt.js";
import ReloadButton from "@/components/Status/ReloadButton.vue";
import RebootButton from "@/components/Status/RebootButton.vue";
import ShutdownButton from "@/components/Status/ShutdownButton.vue";
import DashBoardCard from "@/components/DashBoardCard.vue";

export default {
  name: "StatusView",
  components: {
    ReloadButton,
    RebootButton,
    ShutdownButton,
    DashBoardCard,
  },
  props: {
    changesLocked: { required: false, type: Boolean, default: false },
  },
  data() {
    return {
      mqttStore: useMqttStore(),
    };
  },
};
</script>

<template>
  <dash-board-card color="primary">
    <template #headerLeft>
      Status
    </template>
    <i-container>
      <i-form>
        <i-row>
          <i-column>
            <i-form-group>
              <i-row class="_margin-top:2">
                <i-column
                  xl="2"
                  lg="3"
                  md="4"
                >
                  <i-form-label> IP-Adresse </i-form-label>
                </i-column>
                <i-column>
                  <i-input
                    id="input_system_ip"
                    plaintext
                    :model-value="mqttStore.getSystemIp"
                  />
                </i-column>
              </i-row>
              <i-row class="_margin-top:1">
                <i-column
                  xl="2"
                  lg="3"
                  md="4"
                >
                  <i-form-label> Systemzeit </i-form-label>
                </i-column>
                <i-column>
                  <i-input
                    id="input_system_time"
                    plaintext
                    :model-value="mqttStore.getSystemTime"
                  />
                </i-column>
              </i-row>
              <i-row class="_margin-top:1">
                <i-column
                  xl="2"
                  lg="3"
                  md="4"
                >
                  <i-form-label> Version </i-form-label>
                </i-column>
                <i-column>
                  <i-input
                    id="input_system_version"
                    plaintext
                    :model-value="mqttStore.getSystemVersion"
                  />
                </i-column>
              </i-row>
              <i-row class="_margin-top:1">
                <i-column
                  xl="2"
                  lg="3"
                  md="4"
                >
                  <i-form-label> Version (Details) </i-form-label>
                </i-column>
                <i-column>
                  <i-input
                    id="input_system_commit"
                    plaintext
                    :model-value="mqttStore.getSystemCurrentCommit"
                  />
                </i-column>
              </i-row>
              <i-row class="_margin-top:1">
                <i-column
                  xl="2"
                  lg="3"
                  md="4"
                >
                  <i-form-label> Entwicklungszweig </i-form-label>
                </i-column>
                <i-column>
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
        <i-row
          v-if="!changesLocked"
          class="_margin-top:5"
          between
        >
          <i-column>
            <reload-button block />
          </i-column>
        </i-row>
        <i-row
          v-if="!changesLocked"
          between
        >
          <i-column>
            <reboot-button
              block
              class="_margin-top:2"
            />
          </i-column>
          <i-column>
            <shutdown-button
              block
              class="_margin-top:2"
            />
          </i-column>
        </i-row>
      </i-form>
    </i-container>
  </dash-board-card>
</template>

<style scoped></style>
