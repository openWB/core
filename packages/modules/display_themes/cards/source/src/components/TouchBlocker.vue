<script>
import { useMqttStore } from "@/stores/mqtt.js";

export default {
  name: "TouchBlocker",
  data() {
    return {
      mqttStore: useMqttStore(),
      show: false,
      touchBlockerCountdown: undefined,
      touchBlockerCountdownInterval: undefined,
      defaultViewCountdown: undefined,
      defaultViewCountdownInterval: undefined,
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
    configuredDefaultViewTimeout() {
      if (this.mqttStore.getDefaultViewTimeout === 0 || this.mqttStore.getDefaultViewTimeout === undefined) {
        return undefined;
      }
      return this.mqttStore.getDefaultViewTimeout;
    },
    touchBlockerTimeout() {
      // show touch blocker right before the configured standby time
      return Math.max(this.configuredDisplayStandby - 3, 1);
    },
    defaultViewTimeout() {
      // switch to default view after the configured timeout
      return this.configuredDefaultViewTimeout;
    },
  },
  mounted() {
    this.setupEventHandler();
    this.setupTouchBlockerTimeout();
    this.setupDefaultViewTimeout();
  },
  unmounted() {
    this.clearEventHandler();
    this.clearTouchBlockerTimeout();
    this.clearDefaultViewTimeout();
  },
  methods: {
    handleTouchBlockerClick(event) {
      if (event === false) {
        this.show = false;
        this.setupEventHandler();
        this.setupTouchBlockerTimeout();
        this.setupDefaultViewTimeout();
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
    setupTouchBlockerTimeout() {
      if (this.touchBlockerCountdownCountdownInterval === undefined) {
        this.touchBlockerCountdownCountdownInterval = setInterval(this.updateTouchBlockerCountdown, 1000);
      }
    },
    clearTouchBlockerTimeout() {
      if (this.touchBlockerCountdownCountdownInterval !== undefined) {
        clearInterval(this.touchBlockerCountdownCountdownInterval);
        this.touchBlockerCountdownCountdownInterval = undefined;
      }
    },
    updateTouchBlockerCountdown() {
      if (this.touchBlockerCountdown === undefined) {
        this.touchBlockerCountdown = this.touchBlockerTimeout;
      } else {
        this.touchBlockerCountdown -= 1;
        if (this.touchBlockerCountdown < 1) {
          this.showTouchBlocker();
        }
      }
    },
    setupDefaultViewTimeout() {
      if (
        this.defaultViewCountdownInterval === undefined
        && this.mqttStore.getDefaultView !== this.$route.name
        && this.defaultViewTimeout !== undefined
      ) {
        this.defaultViewCountdownInterval = setInterval(this.updateDefaultViewCountdown, 1000);
      }
    },
    clearDefaultViewTimeout() {
      if (this.defaultViewCountdownInterval !== undefined) {
        clearInterval(this.defaultViewCountdownInterval);
        this.defaultViewCountdownInterval = undefined;
      }
    },
    updateDefaultViewCountdown() {
      if (this.defaultViewCountdown === undefined && this.defaultViewTimeout !== undefined) {
        this.defaultViewCountdown = this.defaultViewTimeout;
      } else {
        if (this.$route.name === this.mqttStore.getDefaultView) {
          this.clearDefaultViewTimeout();
        } else {
          this.defaultViewCountdown -= 1;
          if (this.defaultViewCountdown < 1) {
            this.showDefaultView();
          }
        }
      }
    },
    handleDocumentEvent() {
      this.touchBlockerCountdown = this.touchBlockerTimeout;
      this.defaultViewCountdown = this.defaultViewTimeout;
      this.setupDefaultViewTimeout();
      this.show = false;
    },
    showTouchBlocker() {
      this.show = true;
      this.clearTouchBlockerTimeout();
    },
    showDefaultView() {
      console.log("switching to default view:", this.mqttStore.getDefaultView);
      this.clearDefaultViewTimeout();
      if (this.$route.name !== this.mqttStore.getDefaultView) {
        this.$router.push({ name: this.mqttStore.getDefaultView });
      }
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
