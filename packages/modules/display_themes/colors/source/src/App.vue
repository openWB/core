<template>
	<div class="fixeddisplay">
		<DisplayTheme></DisplayTheme>
		<NavigationBar></NavigationBar>
	</div>
</template>

<script setup lang="ts">
import NavigationBar from './views/NavigationBar.vue'
import DisplayTheme from './views/DisplayTheme.vue'

//import { RouterLink, RouterView } from 'vue-router'
//import HelloWorld from './components/HelloWorld.vue'
// methods
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
