<template>
	<div>
		<button
			v-for="(element, index) in options"
			:id="'radio-' + element[1]"
			:key="index"
			class="btn btn-outline-secondary radiobutton me-2 mb-0 px-2"
			:value="element[1]"
			:style="getColor(index)"
			:class="element[1] == v ? 'active' : ''"
			@click="setValue"
		>
			<span :style="getColor(index)">
				<i v-if="element[3]" class="fa-solid" :class="element[3]" />
				{{ element[0] }}
			</span>
		</button>
	</div>
	<!-- 
<div class="form-check">
   <span v-for="(element, index) in options">
    <input
      class="btn-check"
      type="radio"
      name="foo"
      :id="'radio-' + element[1]"
      autocomplete="off"
      :value="element[1]"
      v-on:change="showValue"
    />
    <label
      class="btn me-1 px-1 mb-1 btn-outline-secondary selectButton"
      :for="'radio' + element[1]"
    >
      <span :style="getColor(index)">
        <i class="fa-solid" :class="getIcon(index)"></i>
        {{ element[0] }}
      </span>
    </label>
  </span>
  </div>
  -->
	<!--
   <div>
  <div class="form-check-inline" v-for="(element, index) in options">
    <input
      class="form-check-input"
      type="radio"
      :id="'radio-' + element[1]"
      :value="element[1]"
      v-model="v"
    />
    <label class="form-check-label" :for="'radio' + element[1]">
      <span :style="getColor(index)">
        <i class="fa-solid" :class="getIcon(index)"></i>
        {{ element[0] }}
      </span>
    </label>
  </div>
  </div>
  -->
</template>

<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{
	options: [number | string, number | string, string?, string?][]
	modelValue: number | string
}>()
const emit = defineEmits(['update:modelValue'])
const v = computed({
	get() {
		return props.modelValue
	},
	set(value: number | string) {
		emit('update:modelValue', value)
	},
})
function getColor(index: number) {
	if (props.options[index][2]) {
		return { color: props.options[index][2] }
	} else {
		return { color: 'var(--color-fg)' }
	}
}
function setValue(event: Event) {
	let element = event.target as HTMLButtonElement
	while (element && !element.value && element.parentElement) {
		// we need to move up the DOM in case a sub element of the button was clicked
		element = element.parentElement as HTMLButtonElement
	}
	if (element.value) {
		v.value = element.value
	}
}
</script>

<style scoped>
.radiobutton {
	border: 0.5px solid var(--color-input);
	opacity: 0.5;
	font-size: var(--font-settings);
}
.btn-outline-secondary.active {
	background-color: var(--color-bg);
	border: 1px solid var(--color-fg);
	box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
	opacity: 1;
}
</style>
