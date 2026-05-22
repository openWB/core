<template>
  <div class="device-sunenergyxt">
    <openwb-base-heading>
      Einstellungen für SunEnergyXT 500 Series
    </openwb-base-heading>
    <openwb-base-text-input
      title="IP-Adresse oder Hostname"
      subtype="host"
      required
      :model-value="device.configuration.ip_address"
      @update:model-value="
        updateConfiguration($event, 'configuration.ip_address')
      "
    >
      <template #help>
        IP-Adresse des SunEnergyXT-Geräts im lokalen Netzwerk
      </template>
    </openwb-base-text-input>
    <openwb-base-number-input
      title="Port"
      :min="1"
      :max="65535"
      required
      :model-value="device.configuration.port"
      @update:model-value="
        updateConfiguration($event, 'configuration.port')
      "
    >
      <template #help>
        HTTP-Port des Geräts (Standard: 80)
      </template>
    </openwb-base-number-input>
    <openwb-base-number-input
      title="Timeout"
      :min="1"
      :max="30"
      required
      :model-value="device.configuration.timeout"
      @update:model-value="
        updateConfiguration($event, 'configuration.timeout')
      "
    >
      <template #help>
        HTTP-Timeout in Sekunden (Standard: 5)
      </template>
    </openwb-base-number-input>
  </div>
</template>

<script>
import DeviceConfigMixin from "../../DeviceConfigMixin.vue";
export default {
  name: "DeviceSunEnergyXT",
  mixins: [DeviceConfigMixin],
};
</script>
