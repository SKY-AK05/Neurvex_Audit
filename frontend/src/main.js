import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import "./style.css";
import { msalInstance } from "./authConfig";

// Initialize MSAL and process any redirect response
msalInstance.initialize().then(() => {
    msalInstance.handleRedirectPromise().then((response) => {
        if (response && response.account) {
            const email = response.account.username;
            fetch("/api/auth/verify", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email })
            }).then(res => {
                // Guard: if the backend is down or not proxied, res is a 404/HTML page
                // Calling .json() on it causes "Unexpected end of JSON input"
                if (!res.ok) {
                    throw new Error(`Backend returned ${res.status}. Is the Azure Functions host running on port 7071?`);
                }
                return res.json();
            }).then(data => {
                if (data.authorized) {
                    sessionStorage.setItem("nd_auth", "1");
                    sessionStorage.setItem("nd_user_name", response.account.name || email);
                    sessionStorage.setItem("nd_role", data.role);
                    sessionStorage.removeItem("nd_auth_error");

                    const app = createApp(App).use(router);
                    app.mount("#app");
                    router.push("/admin/dashboard");
                } else {
                    sessionStorage.setItem("nd_auth_error", "Access Denied: Your email is not authorised to access this portal.");
                    // Log out of MSAL to clear their invalid session
                    msalInstance.logoutRedirect({ postLogoutRedirectUri: window.location.origin + "/#/admin" });
                }
            }).catch(error => {
                console.error("Backend verification error:", error);
                const msg = error.message.includes("7071")
                    ? "Backend is not running. Start the Azure Functions host and try again."
                    : "Server error during verification. Please try again.";
                sessionStorage.setItem("nd_auth_error", msg);
                const app = createApp(App).use(router);
                app.mount("#app");
                router.push("/admin");
            });
        } else {
            // Not a redirect response (normal page load)
            const app = createApp(App).use(router);
            app.mount("#app");
        }
    }).catch(error => {
        console.error("Auth redirect error:", error);
        sessionStorage.setItem("nd_auth_error", error.message || "Authentication failed.");
        createApp(App).use(router).mount("#app");
    });
}).catch(console.error);
