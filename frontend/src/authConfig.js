import { PublicClientApplication } from "@azure/msal-browser";

export const loginRequest = {
    scopes: ["User.Read"],
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
                    postLogoutRedirectUri: window.location.origin,
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
