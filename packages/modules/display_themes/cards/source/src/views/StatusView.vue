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
};
</script>

<template>Status</template>

<style scoped></style>
