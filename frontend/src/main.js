import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import "./style.css";
import { getMsalInstance } from "./authConfig";

function mountApp() {
    createApp(App).use(router).mount("#app");
}

function isMsalRedirect() {
    const hash = window.location.hash || "";
    return hash.includes("code=") || hash.includes("error=");
}

async function handleAuthRedirect() {
    if (!isMsalRedirect()) {
        mountApp();
        return;
    }

    try {
        const msalInstance = await getMsalInstance();
        const response = await msalInstance.handleRedirectPromise();
        if (response && response.account) {
            const email = response.account.username;
            const res = await fetch("/api/auth/verify", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email }),
            });
            if (!res.ok) {
                throw new Error(`Backend returned ${res.status}. Is the FastAPI backend running?`);
            }
            const data = await res.json();
            mountApp();
            if (data.authorized) {
                sessionStorage.setItem("nd_auth", "1");
                sessionStorage.setItem("nd_user_name", response.account.name || email);
                sessionStorage.setItem("nd_role", data.role);
                sessionStorage.setItem("nd_auth_token", response.idToken);
                sessionStorage.removeItem("nd_auth_error");
                router.push("/admin/dashboard");
            } else {
                sessionStorage.setItem(
                    "nd_auth_error",
                    "Access Denied: Your email is not authorised to access this portal."
                );
                Object.keys(sessionStorage)
                    .filter((k) => k.startsWith("msal.") || k.includes("login.windows"))
                    .forEach((k) => sessionStorage.removeItem(k));
                router.push("/portal");
            }
            return;
        }
        mountApp();
    } catch (error) {
        console.error("Auth redirect error:", error);
        sessionStorage.setItem("nd_auth_error", error.message || "Authentication failed.");
        mountApp();
    }
}

handleAuthRedirect();
