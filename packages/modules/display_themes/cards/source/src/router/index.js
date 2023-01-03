import { createRouter, createWebHistory } from "vue-router";
import DashBoardView from "../views/DashBoardView.vue";

const router = createRouter({
	history: createWebHistory(import.meta.env.BASE_URL),
	routes: [
		{
			path: "/",
			alias: "/DashBoard",
			name: "dash-board",
			component: DashBoardView,
		},
		{
			path: "/ChargePoints",
			name: "charge-points",
			// route level code-splitting
			// this generates a separate chunk (ChargePoints.[hash].js) for this route
			// which is lazy-loaded when the route is visited.
			component: () => import("../views/ChargePointsView.vue"),
		},
		{
			path: "/Status",
			name: "status",
			component: () => import("../views/StatusView.vue"),
		},
	],
});

export default router;
