import { createRouter, createWebHistory } from "vue-router";
import HomePage from "./pages/HomePage.vue";
import ReportPage from "./pages/ReportPage.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "home",
      component: HomePage,
    },
    {
      path: "/report/:jobId",
      name: "report",
      component: ReportPage,
      props: true,
    },
  ],
});
