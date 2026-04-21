(function () {
    const api = window.ZestMartApi;
    const utils = window.ZestMartUtils;
    let verifiedPhone = null;

    document.addEventListener("DOMContentLoaded", async () => {
        await utils.redirectIfAuthenticated();
        bindTabs();
        bindForms();
    });

    function bindTabs() {
        const tabButtons = document.querySelectorAll("[data-auth-tab]");
        tabButtons.forEach((button) => {
            button.addEventListener("click", () => activateTab(button.dataset.authTab));
        });
    }

    function activateTab(viewName) {
        document.querySelectorAll("[data-auth-tab]").forEach((button) => {
            button.classList.toggle("is-active", button.dataset.authTab === viewName);
        });

        document.querySelectorAll("[data-auth-view]").forEach((form) => {
            form.classList.toggle("hidden", form.dataset.authView !== viewName);
        });

        utils.showMessage("page-status", "");
        if (viewName !== "student-register") {
            utils.showMessage("otp-status", "");
        }
    }

    function bindForms() {
        document.getElementById("student-login-form").addEventListener("submit", handleStudentLogin);
        document.getElementById("staff-login-form").addEventListener("submit", handleStaffLogin);
        document.getElementById("student-register-form").addEventListener("submit", handleStudentRegister);
        document.getElementById("send-otp-button").addEventListener("click", handleSendOtp);
        document.getElementById("verify-otp-button").addEventListener("click", handleVerifyOtp);
    }

    async function handleStudentLogin(event) {
        event.preventDefault();
        const button = event.currentTarget.querySelector('button[type="submit"]');
        const phone = document.getElementById("student-login-phone").value;
        const password = document.getElementById("student-login-password").value;

        try {
            utils.setButtonBusy(button, true, "Signing in...");
            const response = await api.post("/auth/login/student", { phone, password });
            utils.setCurrentUser(response.data.user);
            window.location.href = "/student";
        } catch (error) {
            utils.showMessage("page-status", error.message, "error");
        } finally {
            utils.setButtonBusy(button, false);
        }
    }

    async function handleStaffLogin(event) {
        event.preventDefault();
        const button = event.currentTarget.querySelector('button[type="submit"]');
        const userId = document.getElementById("staff-login-user-id").value.trim();
        const password = document.getElementById("staff-login-password").value;

        try {
            utils.setButtonBusy(button, true, "Signing in...");
            const response = await api.post("/auth/login/staff", { userId, password });
            utils.setCurrentUser(response.data.user);
            window.location.href = utils.getDashboardRoute(response.data.user.role);
        } catch (error) {
            utils.showMessage("page-status", error.message, "error");
        } finally {
            utils.setButtonBusy(button, false);
        }
    }

    async function handleSendOtp() {
        const button = document.getElementById("send-otp-button");
        const phone = document.getElementById("register-phone").value;
        verifiedPhone = null;

        try {
            utils.setButtonBusy(button, true, "Sending...");
            const response = await api.post("/auth/send-otp", { phone });
            const fragments = [];
            if (response.data.deliveryMode === "mock") {
                fragments.push(`Demo mode is enabled. OTP was generated for ${response.data.maskedPhone} but not sent by SMS.`);
            } else {
                fragments.push(`OTP sent to ${response.data.maskedPhone}.`);
            }
            fragments.push(`Expires in ${response.data.expiresInMinutes} minutes.`);
            if (response.data.deliveryMode === "mock" && response.data.otpPreview) {
                fragments.push(`Use this mock OTP: ${response.data.otpPreview}`);
            }
            utils.showMessage("otp-status", fragments.join(" "), "info");
        } catch (error) {
            utils.showMessage("otp-status", error.message, "error");
        } finally {
            utils.setButtonBusy(button, false);
        }
    }

    async function handleVerifyOtp() {
        const button = document.getElementById("verify-otp-button");
        const phone = document.getElementById("register-phone").value;
        const otp = document.getElementById("register-otp").value;

        try {
            utils.setButtonBusy(button, true, "Verifying...");
            await api.post("/auth/verify-otp", { phone, otp });
            verifiedPhone = utils.normalizePhone(phone);
            utils.showMessage("otp-status", "OTP verified. You can complete registration now.", "success");
        } catch (error) {
            verifiedPhone = null;
            utils.showMessage("otp-status", error.message, "error");
        } finally {
            utils.setButtonBusy(button, false);
        }
    }

    async function handleStudentRegister(event) {
        event.preventDefault();
        const button = event.currentTarget.querySelector('button[type="submit"]');
        const name = document.getElementById("register-name").value.trim();
        const phone = document.getElementById("register-phone").value;
        const password = document.getElementById("register-password").value;
        const address = document.getElementById("register-address").value.trim();

        if (utils.normalizePhone(phone) !== verifiedPhone) {
            utils.showMessage("otp-status", "Verify the OTP for this phone number before registering.", "error");
            return;
        }

        try {
            utils.setButtonBusy(button, true, "Creating account...");
            const response = await api.post("/auth/register", { name, phone, password, address });
            utils.setCurrentUser(response.data.user);
            window.location.href = "/student";
        } catch (error) {
            utils.showMessage("otp-status", error.message, "error");
        } finally {
            utils.setButtonBusy(button, false);
        }
    }
})();
