(function () {
    const { routes } = window.ZestMartConfig;

    let currentUser = null;
    let sessionLoaded = false;
    let pendingSessionRequest = null;

    function resolveElement(target) {
        if (!target) {
            return null;
        }
        if (typeof target === "string") {
            return document.getElementById(target);
        }
        return target;
    }

    function showMessage(target, message, tone) {
        const element = resolveElement(target);
        if (!element) {
            return;
        }

        if (!message) {
            element.textContent = "";
            element.classList.add("hidden");
            element.removeAttribute("data-tone");
            return;
        }

        element.textContent = message;
        element.dataset.tone = tone || "info";
        element.classList.remove("hidden");
    }

    function setCurrentUser(user) {
        currentUser = user || null;
        sessionLoaded = true;
    }

    function resetCurrentUser() {
        currentUser = null;
        sessionLoaded = false;
        pendingSessionRequest = null;
    }

    async function loadSession(forceRefresh) {
        if (sessionLoaded && !forceRefresh) {
            return currentUser;
        }

        if (pendingSessionRequest && !forceRefresh) {
            return pendingSessionRequest;
        }

        pendingSessionRequest = window.ZestMartApi
            .get("/auth/session", { auth: true, allowUnauthorized: true })
            .then((response) => {
                setCurrentUser(response.data.user || null);
                return currentUser;
            })
            .catch((error) => {
                if (error.status === 401) {
                    setCurrentUser(null);
                    return null;
                }
                sessionLoaded = false;
                throw error;
            })
            .finally(() => {
                pendingSessionRequest = null;
            });

        return pendingSessionRequest;
    }

    async function clearSession() {
        try {
            await window.ZestMartApi.post("/auth/logout", {}, { allowUnauthorized: true });
        } catch (_error) {
            // Cookie clearing is best-effort on the client side when the session is already invalid.
        } finally {
            setCurrentUser(null);
        }
    }

    function getCurrentUser() {
        return currentUser;
    }

    function getDashboardRoute(role) {
        return routes[role] || "/";
    }

    function redirectToDashboard(user) {
        window.location.href = getDashboardRoute(user.role);
    }

    async function redirectIfAuthenticated() {
        const user = await loadSession();
        if (user) {
            redirectToDashboard(user);
        }
        return user;
    }

    async function guardRoute(allowedRoles) {
        const user = await loadSession();

        if (!user) {
            await clearSession();
            window.location.href = "/";
            return null;
        }

        if (!allowedRoles.includes(user.role)) {
            window.location.href = getDashboardRoute(user.role);
            return null;
        }

        return user;
    }

    function normalizePhone(phone) {
        return String(phone || "").replace(/\D/g, "");
    }

    function setButtonBusy(button, busy, busyText) {
        if (!button) {
            return;
        }

        if (busy) {
            button.disabled = true;
            button.dataset.originalText = button.textContent;
            button.textContent = busyText || "Working...";
            return;
        }

        button.disabled = false;
        if (button.dataset.originalText) {
            button.textContent = button.dataset.originalText;
            delete button.dataset.originalText;
        }
    }

    function bindLogoutButtons() {
        document.querySelectorAll('[data-action="logout"]').forEach((button) => {
            button.addEventListener("click", async () => {
                await clearSession();
                window.location.href = "/";
            });
        });
    }

    function fillUserBadge(nameElementId, roleElementId, user) {
        const nameElement = document.getElementById(nameElementId);
        const roleElement = document.getElementById(roleElementId);

        if (nameElement) {
            nameElement.textContent = user.name || user.userId || user.phone || "User";
        }
        if (roleElement) {
            roleElement.textContent = `(${capitalize(user.role)})`;
        }
    }

    function populateRoleLinks(targetId, user) {
        const element = resolveElement(targetId);
        if (!element) {
            return;
        }

        const links = ['<a class="nav-chip" href="/student">Shopping View</a>'];
        if (user.role === "delivery" || user.role === "admin") {
            links.push('<a class="nav-chip" href="/delivery">Delivery View</a>');
        }
        if (user.role === "admin") {
            links.push('<a class="nav-chip" href="/admin">Admin View</a>');
        }

        element.innerHTML = links.join("");
    }

    function formatCurrency(value) {
        return new Intl.NumberFormat("en-IN", {
            style: "currency",
            currency: "INR",
            maximumFractionDigits: 2
        }).format(Number(value || 0));
    }

    function formatDate(value) {
        if (!value) {
            return "Unknown date";
        }
        return new Intl.DateTimeFormat("en-IN", {
            dateStyle: "medium",
            timeStyle: "short"
        }).format(new Date(value));
    }

    function escapeHtml(value) {
        return String(value || "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#39;");
    }

    function statusPill(status) {
        const safeStatus = escapeHtml(status || "pending");
        return `<span class="status-pill ${safeStatus}">${safeStatus}</span>`;
    }

    function emptyState(message) {
        return `<div class="empty-state">${escapeHtml(message)}</div>`;
    }

    function capitalize(value) {
        if (!value) {
            return "";
        }
        return value.charAt(0).toUpperCase() + value.slice(1);
    }

    function showDemoModeNotice(target) {
        if (!window.ZestMartDemoApi?.isActive()) {
            return;
        }
        showMessage(
            target,
            "Demo mode is active on this deployment. Data is stored in this browser so the site remains usable on Netlify without a separate backend.",
            "info"
        );
    }

    window.ZestMartUtils = {
        bindLogoutButtons,
        capitalize,
        clearSession,
        emptyState,
        escapeHtml,
        fillUserBadge,
        formatCurrency,
        formatDate,
        getCurrentUser,
        getDashboardRoute,
        guardRoute,
        loadSession,
        normalizePhone,
        populateRoleLinks,
        redirectIfAuthenticated,
        resetCurrentUser,
        setButtonBusy,
        setCurrentUser,
        showDemoModeNotice,
        showMessage,
        statusPill
    };
})();
