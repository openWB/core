<template>
	<WbWidgetFlex v-if="!configmode" :variable-width="true">
		<template #title>
			<span class="fa-solid fa-lightbulb">&nbsp;</span>
			Verbraucher
		</template>
		<template #buttons>
			<span
				type="button"
				class="ms-2 ps-1 pt-1"
				@click="configmode = !configmode"
			>
				<span class="fa-solid fa-lg ps-1 fa-ellipsis-vertical" />
			</span>
		</template>
		<div class="subgrid" v-for="[index, dev] in consumers">
			<ConsumerDevice
				v-if="dev.showInList"
				:key="index"
				:device="<Consumer>dev"
			/>
		</div>
	</WbWidgetFlex>
	<WbWidgetFlex v-else :variable-width="true">
		<template #title> Anzeige der Verbraucher </template>
		<template #buttons>
			<span class="ms-2 pt-1" @click="configmode = !configmode">
				<span class="fa-solid fa-lg ps-1 fa-circle-check" />
			</span>
		</template>
		<ConsumerSettings />
	</WbWidgetFlex>
</template>

<script setup lang="ts">
import { type Consumer, consumers } from './model.ts'
import WbWidgetFlex from '@/components/shared/WbWidgetFlex.vue'
import ConsumerDevice from './ConsumerDevice.vue'
import ConsumerSettings from './ConsumerSettings.vue'
import { ref } from 'vue'

const configmode = ref(false)
</script>

<style scoped>
.fa-lightbulb {
	color: var(--color-consumers);
}
</style>
