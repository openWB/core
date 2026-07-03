<script>
import { useMqttStore } from "@/stores/mqtt.js";

export default {
  name: "VehicleSelectModal",
  props: {
    modelValue: { required: true, type: Boolean },
    chargePointId: {
      type: Number,
      required: true,
    },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      mqttStore: useMqttStore(),
    };
  },
  computed: {
    vehicleList() {
      return this.mqttStore.getVehicleList.map((id) => {
        return {
          id: id,
          name: this.mqttStore.getVehicleName(id),
        };
      });
    },
    vehicleColor() {
      return (vehicleId) => {
        return (
          this.mqttStore.getVehicleColor(vehicleId) || "var(--color--teal)"
        );
      };
    },
    vehicleBackground() {
      return (vehicleId, isConnected) => {
        const baseColor = this.vehicleColor(vehicleId);
        const colorAmount = isConnected ? "50%" : "0%";
        return `color-mix(in srgb, ${baseColor} ${colorAmount}, transparent)`;
      };
    },
  },
  methods: {
    setChargePointConnectedVehicle(event) {
      if (
        event.id !=
        this.mqttStore.getChargePointConnectedVehicleId(this.chargePointId)
      ) {
        this.$root.sendTopicToBroker(
          `openWB/chargepoint/${this.chargePointId}/config/ev`,
          event.id,
        );
      }
      // hide modal vehicle select if visible
      // if (this.modalVehicleSelectVisible) {
      //   this.modalVehicleSelectVisible = false;
      // }
    },
  },
};
</script>

<template>
  <i-modal
    :model-value="modelValue"
    class="modal-vehicle-select"
    size="lg"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <template #header>
      Fahrzeug an "{{ mqttStore.getChargePointName(chargePointId) }}" auswählen
    </template>
    <i-form>
      <i-form-group>
        <i-button-group
          vertical
          block
        >
          <i-button
            v-for="vehicle in vehicleList"
            :key="vehicle.id"
            size="lg"
            class="large-button vehicle"
            :style="{
              'border-color': vehicleColor(vehicle.id),
              background: vehicleBackground(
                vehicle.id,
                mqttStore.getChargePointConnectedVehicleId(chargePointId) ==
                  vehicle.id,
              ),
            }"
            :active="
              mqttStore.getChargePointConnectedVehicleId(chargePointId) ==
                vehicle.id
            "
            :color="
              mqttStore.getChargePointConnectedVehicleId(chargePointId) ==
                vehicle.id
                ? 'primary'
                : ''
            "
            @click="setChargePointConnectedVehicle(vehicle)"
          >
            {{ vehicle.name }}
          </i-button>
        </i-button-group>
      </i-form-group>
    </i-form>
  </i-modal>
</template>

<style scoped>
.modal-vehicle-select:deep(.modal-body) {
  max-height: 72vh;
  overflow-y: scroll;
}

.vehicle {
  border-left: 10px solid;
}
</style>
