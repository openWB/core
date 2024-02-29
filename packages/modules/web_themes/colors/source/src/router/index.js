import { createRouter, createWebHistory } from 'vue-router'
import ColorsTheme from '../views/ColorsTheme.vue'
import ThemeSettings from '../views/ThemeSettings.vue'
const routes = [
	{
		path: '/',
		name: 'ColorsTheme',
		component: ColorsTheme,
	},
	{
		path: '/themesettings',
		name: 'ThemeSettings',
		component: ThemeSettings,
	},
]
const router = createRouter({
	history: createWebHistory(import.meta.env.BASE_URL),
	routes,
})
export default router
