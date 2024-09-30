<template>
  <div class="device-sample-counter">
    <openwb-base-heading>
      Einstellungen für Sample Zähler
    </openwb-base-heading>
  </div>
</template>

<script>
import ComponentConfigMixin from "../../ComponentConfigMixin.vue";

export default {
  name: "DeviceSampleCounter",
  mixins: [ComponentConfigMixin],
};
</script>
