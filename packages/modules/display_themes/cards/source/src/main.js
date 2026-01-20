import { createApp } from "vue";
import { createPinia } from "pinia";

import App from "./App.vue";
import router from "./router";

import VueCookies from "vue-cookies";

import { Inkline, components } from "@inkline/inkline";
import "@inkline/inkline/inkline.scss";
import "./main.scss";

const app = createApp(App)
  .use(createPinia())
  .use(router)
  .use(Inkline, {
    colorMode: "dark",
    components,
  })
  .use(VueCookies, {
    expire: "30d",
    path: "/",
    domain: "",
    secure: true,
    sameSite: "Lax",
  });

app.mount("#app");
