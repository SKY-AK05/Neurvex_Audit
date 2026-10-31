import { PublicClientApplication } from "@azure/msal-browser";

export const loginRequest = {
    scopes: ["openid", "profile", "email", "User.Read"],
};

let msalInstancePromise = null;

async function resolveAuthConfig() {
    const clientId = import.meta.env.VITE_MSAL_CLIENT_ID;
    const tenantId = import.meta.env.VITE_MSAL_TENANT_ID;
    if (clientId && tenantId && clientId !== "your-azure-ad-application-client-id") {
        return { clientId, tenantId };
    }

    try {
        const res = await fetch("/api/auth/config");
        if (res.ok) {
            const data = await res.json();
            if (data.clientId && data.tenantId) {
                return { clientId: data.clientId, tenantId: data.tenantId };
            }
        }
    } catch (e) {
        // Backend not running locally
    }

    // Default Entra credentials from root .env fallback
    return {
        clientId: "2f900af5-c166-4fdb-90f1-1eaee09eeff2",
        tenantId: "ea77fe37-fd2c-4294-87c3-8746bce6625a",
    };
}

/** Lazy MSAL instance — loads client ID from build env or /api/auth/config at runtime. */
export async function getMsalInstance() {
    if (!msalInstancePromise) {
        msalInstancePromise = (async () => {
            const { clientId, tenantId } = await resolveAuthConfig();
            const instance = new PublicClientApplication({
                auth: {
                    clientId,
                    authority: `https://login.microsoftonline.com/${tenantId}`,
                    redirectUri: window.location.origin,
                    postLogoutRedirectUri: `${window.location.origin}/portal`,
                },
                cache: {
                    cacheLocation: "sessionStorage",
                    storeAuthStateInCookie: false,
                },
            });
            await instance.initialize();
            return instance;
        })();
    }
    return msalInstancePromise;
}

/** Finish login after MSAL redirect: verify email with backend and store session. */
export async function completeAdminLogin(msalResponse) {
    if (!msalResponse?.account) {
        return { ok: false, reason: "no_account" };
    }

    const idToken = msalResponse.idToken;
    if (!idToken) {
        throw new Error("Microsoft did not return an ID token. Check Entra app registration.");
    }

    const email = (msalResponse.account.username || "").trim().toLowerCase();
    const res = await fetch("/api/auth/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
    });
    if (!res.ok) {
        throw new Error(`Sign-in verification failed (${res.status}). Is the API running?`);
    }
    const data = await res.json();
    if (!data.authorized) {
        return { ok: false, reason: "denied", email };
    }

    sessionStorage.setItem("nd_auth", "1");
    sessionStorage.setItem("nd_user_name", msalResponse.account.name || email);
    sessionStorage.setItem("nd_role", data.role || "admin");
    sessionStorage.setItem("nd_auth_token", idToken);
    sessionStorage.removeItem("nd_auth_error");
    return { ok: true };
}

export function clearMsalCache() {
    Object.keys(sessionStorage)
        .filter((k) => k.startsWith("msal.") || k.includes("login.windows"))
        .forEach((k) => sessionStorage.removeItem(k));
}
