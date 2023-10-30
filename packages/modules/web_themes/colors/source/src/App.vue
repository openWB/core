/* * App.vue * colors theme for openwb 2.0 * Copyright (c) 2022 Claus Hagen */

<template>
	<div id="app" class="m-0 p-0">
		<NavigationBar />
		<div class="p-0" :class="containerclass">
			<div class="row p-0 m-0">
				<div class="col-12 p-0 m-0">
					<ColorsTheme />
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import ColorsTheme from './views/ColorsTheme.vue'
import NavigationBar from './components/NavigationBar.vue'
import { computed } from 'vue'
import { globalConfig } from './assets/js/themeConfig'

const containerclass = computed(() => {
	return globalConfig.fluidDisplay ? 'container-fluid' : 'container-lg'
})
</script>

<style>
@import './assets/css/style.css';
@import './assets/fonts/fontawesome-free-6.0.0-web/css/fontawesome.min.css';
@import './assets/fonts/fontawesome-free-6.0.0-web/css/solid.min.css';
</style>
