<script>
import { useMqttStore } from "@/stores/mqtt.js";
import DashBoardCard from "@/components/DashBoardCard.vue";
import SparkLine from "@/components/SparkLine.vue";
import ChargePointPlugBadge from "@/components/ChargePointPlugBadge.vue";

/* fontawesome */
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { faChargingStation as fasChargingStation } from "@fortawesome/free-solid-svg-icons";
/* add icons to the library */
library.add(fasChargingStation);

export default {
  name: "ChargePointsCard",
  components: {
    DashBoardCard,
    SparkLine,
    FontAwesomeIcon,
    ChargePointPlugBadge,
  },
  props: {},
  data() {
    return {
      mqttStore: useMqttStore(),
    };
  },
};
</script>

<template>
  <dash-board-card
    v-if="mqttStore.getChargePointIds.length > 0"
    color="primary"
  >
    <template #headerLeft>
      <font-awesome-icon
        fixed-width
        :icon="['fas', 'fa-charging-station']"
      />
      {{
        mqttStore.getChargePointIds.length == 1
          ? mqttStore.getChargePointName(mqttStore.getChargePointIds[0])
          : "Ladepunkte"
      }}
    </template>
    <template #headerRight>
      {{
        mqttStore.getChargePointIds.length == 1
          ? mqttStore.getChargePointPower(mqttStore.getChargePointIds[0])
          : mqttStore.getChargePointSumPower()
      }}
      <charge-point-plug-badge
        :charge-point-id="mqttStore.getChargePointIds"
        :show-energy-charged="false"
      />
    </template>
    <spark-line
      color="var(--color--primary)"
      :data="
        mqttStore.getChargePointIds.length == 1
          ? mqttStore.getChargePointPowerChartData(
            mqttStore.getChargePointIds[0],
          )
          : mqttStore.getChargePointSumPowerChartData
      "
    />
  </dash-board-card>
</template>
