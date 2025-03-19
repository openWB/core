<template>
  <div class="vehicle-soc-sample">
    <openwb-base-heading>
      Einstellungen für Sample SoC
    </openwb-base-heading>
  </div>
</template>

<script>
import VehicleConfigMixin from "../VehicleConfigMixin.vue";

export default {
  name: "VehicleSocSample",
  mixins: [VehicleConfigMixin],
  data() {
    return {};
  },
};
</script>
