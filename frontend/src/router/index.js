import { createRouter, createWebHistory } from "vue-router";
import AuditForm        from "../views/AuditForm.vue";
import AdminLogin       from "../views/AdminLogin.vue";
import Overview         from "../views/Overview.vue";
import Submissions      from "../views/Submissions.vue";
import SubmissionDetail from "../views/SubmissionDetail.vue";
import Analytics        from "../views/Analytics.vue";
import Settings         from "../views/Settings.vue";
import Support          from "../views/Support.vue";
import UserManagement   from "../views/UserManagement.vue";
import ResumeDraft      from "../views/ResumeDraft.vue";
import OrgLogin         from "../views/OrgLogin.vue";
import OrgVerify        from "../views/OrgVerify.vue";
import OrgDashboard     from "../views/OrgDashboard.vue";
import Organisations    from "../views/Organisations.vue";

const routes = [
  { path: "/",                        component: AuditForm },
  { path: "/portal",                  component: AdminLogin },
  { path: "/admin",                   redirect: "/portal" },
  { path: "/admin/dashboard",         component: Overview,         meta: { requiresAuth: true } },
  { path: "/admin/submissions",       component: Submissions,      meta: { requiresAuth: true } },
  { path: "/admin/submissions/:id([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})",   component: SubmissionDetail, meta: { requiresAuth: true } },
  { path: "/admin/analytics",         component: Analytics,        meta: { requiresAuth: true } },
  { path: "/admin/settings",          component: Settings,         meta: { requiresAuth: true } },
  { path: "/admin/support",           component: Support,          meta: { requiresAuth: true } },
  { path: "/admin/users",             component: UserManagement,   meta: { requiresAuth: true, requiresSuper: true } },
  { path: "/admin/organisations",     component: Organisations,    meta: { requiresAuth: true } },

  // Public / org routes
  { path: "/resume",                  component: ResumeDraft },
  { path: "/org/login",               component: OrgLogin },
  { path: "/org/verify",              component: OrgVerify },
  { path: "/org/dashboard",           component: OrgDashboard,     meta: { requiresOrgAuth: true } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  if (to.meta.requiresAuth && !sessionStorage.getItem("nd_auth")) {
    return "/portal";
  }
  if (to.meta.requiresSuper && sessionStorage.getItem("nd_role") !== "super") {
    return "/admin/dashboard";
  }
  if (to.meta.requiresOrgAuth && !localStorage.getItem("org_token")) {
    return "/org/login";
  }
});

export default router;
