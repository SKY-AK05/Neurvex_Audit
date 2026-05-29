import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import "./style.css";
import { getMsalInstance, completeAdminLogin, clearMsalCache } from "./authConfig";

function mountApp() {
    createApp(App).use(router).mount("#app");
}

async function handleAuthRedirect() {
    try {
        const msalInstance = await getMsalInstance();
        const response = await msalInstance.handleRedirectPromise();

        if (response?.account) {
            const result = await completeAdminLogin(response);
            if (result.ok) {
                mountApp();
                await router.isReady();
                await router.replace("/admin/dashboard");
                return;
            }
            sessionStorage.setItem(
                "nd_auth_error",
                `Access denied: ${result.email || "your account"} is not in admin_users.`
            );
            clearMsalCache();
        }
    } catch (error) {
        console.error("Auth redirect error:", error);
        sessionStorage.setItem("nd_auth_error", error.message || "Authentication failed.");
        clearMsalCache();
    }

    mountApp();
}

handleAuthRedirect();
