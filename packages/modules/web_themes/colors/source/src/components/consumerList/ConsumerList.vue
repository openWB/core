<template>
	<WbWidgetFlex :variable-width="true">
		<template #title>
			<span class="fa-solid fa-lightbulb">&nbsp;</span>
			Verbraucher
		</template>
		<div class="subgrid" v-for="[index, dev] in consumers">
			<ConsumerDevice
				v-if="dev.showInList"
				:key="index"
				:device="<Consumer>dev"
			/>
		</div>
	</WbWidgetFlex>
</template>

<script setup lang="ts">
import { type Consumer, consumers } from './model.ts'
import WbWidgetFlex from '@/components/shared/WbWidgetFlex.vue'
import ConsumerDevice from './ConsumerDevice.vue'
</script>

<style scoped>
.fa-lightbulb {
	color: var(--color-consumers);
}
</style>
