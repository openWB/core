<template>
	<div class="instantsettings mt-5 grid12">
		<!-- Ampere -->
		<ConfigItem title="Stromstärke" icon="fa-bolt" :fullwidth="true">
			<RangeInput
				id="targetCurrent"
				v-model="cp.instantTargetCurrent"
				:min="6"
				:max="32"
				:step="1"
				unit="A"
			/>
		</ConfigItem>
	</div>
</template>

<script setup lang="ts">
// import { eventBus } from '@/main.js'
import { computed } from 'vue'
import { chargePoints } from './model'
import ConfigItem from '../shared/ConfigItem.vue'
import RangeInput from '@/components/shared/RangeInput.vue'

const props = defineProps<{
	chargepointId: number
}>()

const cp = computed(() => {
	return chargePoints[props.chargepointId]
})



// methods
</script>

<style scoped>
.instantsettings {
	justify-content: center;
	grid-gap: 20px;
}
.chargeConfigSelect {
	background: var(--color-bg);
	color: var(--color-fg);
}
.heading {
	color: var(--color-fg);
	font-size: var(--font-settings);
	font-weight: bold;
}
</style>
