<script>
import { useMqttStore } from "@/stores/mqtt.js";
import DashBoardCard from "@/components/DashBoardCard.vue";
import SparkLine from "@/components/SparkLine.vue";

export default {
	name: "DashBoard",
	data() {
		return {
			mqttStore: useMqttStore(),
		};
	},
	components: { DashBoardCard, SparkLine },
	computed: {
		gridPower() {
			let gridId = 0;
			gridId = this.mqttStore.getGridId;
			if (gridId === undefined) {
				return "---";
			}
			return this.mqttStore.getValueString(
				`openWB/counter/${gridId}/get/power`,
				"W"
			);
		},
		gridPowerChartData() {
			let gridId = 0;
			gridId = this.mqttStore.getGridId;
			if (gridId === undefined) {
				return [];
			}
			return this.mqttStore.chartData[
				`openWB/counter/${gridId}/get/power`
			];
		},
		homePower() {
			return this.mqttStore.getValueString(
				"openWB/counter/set/home_consumption",
				"W"
			);
		},
		homePowerChartData() {
			return this.mqttStore.chartData[
				"openWB/counter/set/home_consumption"
			];
		},
		batteryConfigured() {
			return this.mqttStore.getValueBool("openWB/bat/config/configured");
		},
		batteryPower() {
			return this.mqttStore.getValueString("openWB/bat/get/power", "W");
		},
		batteryPowerChartData() {
			return this.mqttStore.chartData["openWB/bat/get/power"];
		},
		batterySoc() {
			return this.mqttStore.getValueString("openWB/bat/get/soc", "%");
		},
		batterySocChartData() {
			return this.mqttStore.chartData["openWB/bat/get/soc"];
		},
		chargePointSumPower() {
			return this.mqttStore.getValueString(
				"openWB/chargepoint/get/power",
				"W"
			);
		},
		chargePointSumPowerChartData() {
			return this.mqttStore.chartData["openWB/chargepoint/get/power"];
		},
		pvConfigured() {
			return this.mqttStore.getValueBool("openWB/pv/config/configured");
		},
		pvPower() {
			return this.mqttStore.getValueString(
				"openWB/pv/get/power",
				"W",
				true
			);
		},
		pvPowerChartData() {
			return this.mqttStore.chartData["openWB/pv/get/power"].map(
				(point) => {
					return point * -1;
				}
			);
		},
	},
};
</script>

<template>
	<div class="dash-board-card-wrapper">
		<dash-board-card color="danger">
			<template #headerLeft> EVU </template>
			<template #headerRight>
				{{ gridPower }}
			</template>
			<spark-line
				color="var(--color--danger)"
				colorNegative="var(--color--success)"
				:data="gridPowerChartData"
			/>
		</dash-board-card>
		<dash-board-card color="light">
			<template #headerLeft> Hausverbrauch </template>
			<template #headerRight>
				{{ homePower }}
			</template>
			<spark-line
				color="var(--color--light)"
				:data="homePowerChartData"
			/>
		</dash-board-card>
		<dash-board-card color="warning" v-if="batteryConfigured">
			<template #headerLeft> Speicher </template>
			<template #headerRight>
				{{ batteryPower }}
			</template>
			<spark-line
				color="var(--color--warning)"
				:data="batteryPowerChartData"
			/>
		</dash-board-card>
		<dash-board-card color="warning" v-if="batteryConfigured">
			<template #headerLeft> Speicher SoC </template>
			<template #headerRight>
				{{ batterySoc }}
			</template>
			<spark-line
				color="var(--color--warning)"
				:data="batterySocChartData"
				:min="0"
				:max="100"
			/>
		</dash-board-card>
		<dash-board-card color="primary">
			<template #headerLeft> Ladepunkte </template>
			<template #headerRight>
				{{ chargePointSumPower }}
			</template>
			<spark-line
				color="var(--color--primary)"
				:data="chargePointSumPowerChartData"
			/>
		</dash-board-card>
		<dash-board-card color="success" v-if="pvConfigured">
			<template #headerLeft> PV </template>
			<template #headerRight>
				{{ pvPower }}
			</template>
			<spark-line
				color="var(--color--success)"
				:data="pvPowerChartData"
				:inverted="true"
			/>
		</dash-board-card>
	</div>
</template>

<style scoped>
.dash-board-card-wrapper {
	display: flex;
	gap: var(--spacing);
	flex-wrap: wrap;
}

.card {
	min-width: 15rem;
	min-height: 130px;
	flex: 17rem;
	----background: inherit !important;
	----body--color: var(--contrast-color-for-dark-background) !important;
}
</style>
