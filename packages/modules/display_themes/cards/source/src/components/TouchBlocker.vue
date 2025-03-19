<script>
import { useMqttStore } from "@/stores/mqtt.js";

export default {
  name: "TouchBlocker",
  data() {
    return {
      mqttStore: useMqttStore(),
      show: false,
      countdown: undefined,
      countdownInterval: undefined,
      events: ["mousemove", "touchmove", "wheel", "click"],
      eventHandlerSetup: false,
    };
  },
  computed: {
    configuredDisplayStandby() {
      if (this.mqttStore.getDisplayStandby === 0 || this.mqttStore.getDisplayStandby === undefined) {
        return undefined;
      }
      return this.mqttStore.getDisplayStandby;
    },
    touchBlockerTimeout() {
      // show touch blocker right before the configured standby time
      return Math.max(this.configuredDisplayStandby - 3, 1);
    },
  },
  mounted() {
    this.setupEventHandler();
    this.setupTimeout();
  },
  unmounted() {
    this.clearEventHandler();
    this.clearTimeout();
  },
  methods: {
    handleTouchBlockerClick(event) {
      if (event === false) {
        this.show = false;
        this.setupEventHandler();
        this.setupTimeout();
      }
    },
    setupEventHandler() {
      if (!this.eventHandlerSetup) {
        this.events.forEach((event) => {
          document.addEventListener(event, this.handleDocumentEvent, { passive: true });
        });
        this.eventHandlerSetup = true;
      }
    },
    clearEventHandler() {
      if (this.eventHandlerSetup) {
        this.events.forEach((event) => {
          document.removeEventListener(event, this.handleDocumentEvent, { passive: true });
        });
        this.eventHandlerSetup = false;
      }
    },
    setupTimeout() {
      if (this.countdownInterval === undefined) {
        this.countdownInterval = setInterval(this.updateCountdown, 1000);
      }
    },
    clearTimeout() {
      if (this.countdownInterval !== undefined) {
        clearInterval(this.countdownInterval);
        this.countdownInterval = undefined;
      }
    },
    updateCountdown() {
      if (this.countdown === undefined) {
        this.countdown = this.touchBlockerTimeout;
      } else {
        this.countdown -= 1;
        if (this.countdown < 1) {
          this.showTouchBlocker();
        }
      }
    },
    handleDocumentEvent() {
      this.countdown = this.touchBlockerTimeout;
      this.show = false;
    },
    showTouchBlocker() {
      this.show = true;
      this.clearTimeout();
    },
  },
};
</script>

<template>
  <Teleport to="body">
    <IModal
      class="touch-blocker"
      size="sm"
      color="dark"
      :model-value="show"
      @update:model-value="handleTouchBlockerClick($event)"
    >
      <img
        class="logo"
        src="/openWB_logo_dark.png"
      >
      <p>
        Bitte das Display berühren.
      </p>
    </IModal>
  </Teleport>
</template>

<style scoped>
.touch-blocker{
  backdrop-filter: blur(5px);
}

:deep(.modal) {
  box-shadow: none;
}

:deep(.modal > .modal-body) {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: transparent;
  border: none;
}
</style>
