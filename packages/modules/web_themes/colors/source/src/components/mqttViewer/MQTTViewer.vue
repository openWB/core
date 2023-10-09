<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { msgInit } from './processMessages'
import { topicForest } from './model'
import Node from './MqttNode.vue'

onMounted(() => {
	msgInit()
})

const expandAll = ref(false)
function toggle() {
	expandAll.value = !expandAll.value
}
const isActive = computed(() => {
	if (expandAll.value) {
		return 'active'
	} else {
		return ''
	}
})
</script>

<template>
	<div class="mqviewer">
		<div class="row pt-2">
			<div class="col">
				<h3 class="mqtitle ps-2">MQTT Message Viewer</h3>
				<hr />
				<button
					class="btn btn-small btn-outline-primary ms-2"
					:class="isActive"
					@click="toggle"
				>
					Expand All
				</button>
				<hr />
			</div>
		</div>
		<div v-if="topicForest[0]">
			<Node
				v-for="(node, i) in topicForest[0].children.sort((n1, n2) =>
					n1.name < n2.name ? -1 : 1,
				)"
				:key="i"
				:node="node"
				:level="1"
				:hide="true"
				:expand-all="expandAll"
			/>
		</div>
	</div>
</template>

<style scoped>
.mqviewer {
	background-color: white;
	color: black;
}

.mqtitle {
	color: black;
}
</style>
