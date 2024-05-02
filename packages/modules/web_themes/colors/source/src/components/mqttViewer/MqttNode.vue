<template>
	<div class="name py-2 px-2 m-0" :style="leafStyle" @click="toggle">
		<span
			v-if="((expanded || props.expandAll) && childCount > 0) || showContent"
			class="fas fa-caret-down"
		></span>
		<span v-else class="fas fa-caret-right"></span>
		{{ displaytext }}{{ counter }}
	</div>
	<div v-if="showContent" class="content p-2 m-2">
		<code>{{ props.node.lastValue }}</code>
	</div>

	<div
		v-if="(expanded || props.expandAll) && childCount > 0"
		class="sublist col-md-9 m-0 p-0 ps-2"
	>
		<MqttNode
			v-for="(child, i) in items"
			:key="i"
			:level="props.level + 1"
			:node="child"
			:hide="true"
			:expand-all="props.expandAll"
		/>
	</div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Node } from './model'
const props = defineProps<{
	node: Node
	level: number
	hide: boolean
	expandAll: boolean
}>()
let expanded = ref(!props.hide)
let showContent = ref(false)
const displaytext = computed(() => {
	return props.node.name
})
const items = computed(() => {
	return [...props.node.children].sort((n1, n2) => (n1.name < n2.name ? -1 : 1))
})
const counter = computed(() => {
	if (props.node.count > 0) {
		return '(' + props.node.count + ')'
	} else {
		return ''
	}
})
const childCount = computed(() => {
	return props.node.children.length
})
const leafStyle = computed(() => {
	if (props.node.lastValue != '') {
		return {
			'font-style': 'italic',
			'grid-column-start': props.level,
			'grid-column-end': -1,
		}
	} else {
		return {
			'grid-column-start': props.level,
			'grid-column-end': -1,
		}
	}
})
function toggle() {
	if (childCount.value > 0) {
		expanded.value = !expanded.value
	}
	if (props.node.lastValue != '') {
		showContent.value = !showContent.value
	}
}
</script>

<style scoped>
.name {
	font-size: 1rem;
	color: black;
	border: 1px solid white;
}

.content {
	grid-column: 1 / -1;
	border: solid 1px black;
	border-radius: 10px;
}

.sublist {
	grid-column: 1 / -1;
	display: grid;
	grid-template-columns: subgrid;
}
</style>
