import { PublicClientApplication } from "@azure/msal-browser";

export const loginRequest = {
    scopes: ["openid", "profile", "email", "User.Read"],
};

let msalInstancePromise = null;

async function resolveAuthConfig() {
    const clientId = import.meta.env.VITE_MSAL_CLIENT_ID;
    const tenantId = import.meta.env.VITE_MSAL_TENANT_ID;
    if (clientId && tenantId) {
        return { clientId, tenantId };
    }

    const res = await fetch("/api/auth/config");
    if (!res.ok) {
        throw new Error("Could not load sign-in configuration from the server.");
    }
    const data = await res.json();
    if (!data.clientId || !data.tenantId) {
        throw new Error(
            "Microsoft sign-in is not configured. Set ENTRA_CLIENT_ID and ENTRA_TENANT_ID on the server."
        );
    }
    return { clientId: data.clientId, tenantId: data.tenantId };
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
