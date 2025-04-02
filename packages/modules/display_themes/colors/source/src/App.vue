<template>
	<div class="fixeddisplay">
		<DisplayTheme></DisplayTheme>
		<NavigationBar></NavigationBar>
	</div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import NavigationBar from './views/NavigationBar.vue'
import DisplayTheme from './views/DisplayTheme.vue'
import { wbSettings } from './assets/js/themeConfig'

onMounted(() => {
	console.log('on mounted')
	let uri = window.location.search
	if (uri != '') {
		console.debug('search', uri)
		let params = new URLSearchParams(uri)
		if (params.has('data')) {
			let data = JSON.parse(params.get('data')!)
			Object.entries(data).forEach(([key, value]) => {
				console.log('updateSetting', key, value)
				if (key.startsWith('parentChargePoint')) {
					wbSettings[key] = parseInt(value as string)
				} else {
					wbSettings[key] = value as string
				}
			})
		}
	}
})
</script>

<style>
@import './assets/css/style.css';
@import './assets/fonts/fontawesome-free-6.0.0-web/css/fontawesome.min.css';
@import './assets/fonts/fontawesome-free-6.0.0-web/css/solid.min.css';
</style>
<style scoped>
.fixeddisplay {
	display: grid;
	grid-template-rows: 440px 40px;
	grid-template-columns: 800px;
}
</style>
