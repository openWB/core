<script>
/* fontawesome */
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import {
  faLock as fasLock,
  faLockOpen as fasLockOpen,
  faDeleteLeft as fasDeleteLeft,
  faEraser as fasEraser,
} from "@fortawesome/free-solid-svg-icons";
/* add icons to the library */
library.add(fasLock, fasLockOpen, fasDeleteLeft, fasEraser);

import { useMqttStore } from "@/stores/mqtt.js";
import CodeInputModal from "./CodeInputModal.vue";

export default {
  name: "LockNavItem",
  props: {},
  data() {
    return {
      mqttStore: useMqttStore(),
      modalPinEntryVisible: false,
      modalPinEntryColor: "warning",
      code: "",
      countdown: 0,
      countdownInterval: undefined,
      events: ["mousemove", "touchmove", "wheel"],
    };
  },
  components: {
    FontAwesomeIcon,
    CodeInputModal,
  },
  computed: {
    changesLocked: {
      get() {
        return this.mqttStore.settings.changesLocked;
      },
      set(value) {
        this.mqttStore.settings.changesLocked = value;
      },
    },
    timer() {
      return (
        Math.trunc(this.countdown / 60).toString() +
        ":" +
        (this.countdown % 60).toString().padStart(2, "0")
      );
    },
  },
  methods: {
    toggleChangesLock() {
      if (this.changesLocked) {
        this.unlockChanges();
      } else {
        this.lockChanges();
      }
    },
    unlockChanges() {
      this.modalPinEntryVisible = true;
    },
    checkUnlockCode(event) {
      console.log("checkUnlockCode", event);
      if (this.mqttStore.checkChangesLockCode(event)) {
        this.$refs.lockInput.success("success");
        this.changesLocked = false;
        if (this.mqttStore.getDisplayStandby > 0) {
          this.countdown = this.mqttStore.getDisplayStandby;
          this.countdownInterval = setInterval(this.updateCountdown, 1000);
          this.events.forEach((event) => {
            document.addEventListener(event, this.handleDocumentEvent, {
              passive: true,
            });
          });
        }
      } else {
        console.warn("check unlock code failed!");
        this.$refs.lockInput.error("danger");
      }
    },
    lockChanges() {
      this.changesLocked = true;
      this.events.forEach((event) => {
        document.removeEventListener(event, this.handleDocumentEvent, {
          passive: true,
        });
      });
      if (this.countdownInterval !== undefined) {
        clearInterval(this.countdownInterval);
        this.countdownInterval = undefined;
      }
    },
    updateCountdown() {
      this.countdown -= 1;
      if (this.countdown < 1) {
        this.lockChanges();
      }
    },
    handleDocumentEvent() {
      this.countdown = this.mqttStore.getDisplayStandby;
    },
  },
  mounted() {
    // init in locked state
    this.changesLocked = true;
  },
};
</script>

<template>
  <i-button
    v-if="mqttStore.getLockChanges"
    @click="toggleChangesLock()"
    class="_padding-left:0 _padding-right:0 _margin-bottom:1"
    size="lg"
    block
    :color="this.changesLocked ? 'danger' : 'success'"
  >
    <FontAwesomeIcon
      fixed-width
      :icon="this.changesLocked ? ['fas', 'fa-lock'] : ['fas', 'fa-lock-open']"
      :class="this.changesLocked ? '_color:danger-80' : '_color:success-80'"
    />
    <span v-if="!changesLocked && countdownInterval" class="_padding-left:1">
      {{ timer }}
    </span>
  </i-button>
  <!-- modals -->
  <CodeInputModal
    v-model="modalPinEntryVisible"
    @update:input-value="checkUnlockCode"
    ref="lockInput"
    :minLength="4"
    :maxLength="10"
  >
    <template #header>
      Bitte den PIN zur Freigabe von Änderungen eingeben.
    </template>
  </CodeInputModal>
</template>

<style scoped></style>
