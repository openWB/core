<template>
	<div class="mt-2">
		<p class="heading ms-1">Sofortladen:</p>

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
import { ref } from 'vue'
import type { ChargePoint } from '../model'
import ConfigItem from '../../shared/ConfigItem.vue'
import RangeInput from '@/components/shared/RangeInput.vue'
const props = defineProps<{
	chargepoint: ChargePoint
}>()
const cp = ref(props.chargepoint)

// methods
</script>

<style scoped>
.chargeConfigSelect {
	background: var(--color-bg);
	color: var(--color-fg);
}
.heading {
	color: var(--color-charging);
}
</style>
