import { createRouter, createWebHashHistory } from "vue-router";
import WelcomeView from "../views/WelcomeView.vue";

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "welcome",
      component: WelcomeView,
    },
    {
      path: "/DashBoard",
      name: "dash-board",
      // route level code-splitting
      // this generates a separate chunk (DashBoardView.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import("../views/DashBoardView.vue"),
    },
    {
      path: "/ChargePoints",
      name: "charge-points",
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
