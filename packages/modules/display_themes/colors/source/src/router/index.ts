import { createRouter, createWebHistory } from 'vue-router'
import DisplayTheme from '../views/DisplayTheme.vue'

const router = createRouter({
	history: createWebHistory(import.meta.env.BASE_URL),
	routes: [
		{
			path: '/',
			name: 'home',
			component: DisplayTheme,
		},
	],
})

export default router
