(function () {
    const config = window.ZestMartConfig;

    async function request(path, options) {
        const {
            method = "GET",
            body,
            auth = false,
            allowUnauthorized = false,
            formData = false,
            headers = {}
        } = options || {};

        const requestHeaders = { ...headers };
        const fetchOptions = {
            method,
            headers: requestHeaders,
            credentials: "include"
        };

        if (body !== undefined) {
            if (formData) {
                fetchOptions.body = body;
            } else {
                requestHeaders["Content-Type"] = "application/json";
                fetchOptions.body = JSON.stringify(body);
            }
        }

        const response = await fetch(`${config.apiBaseUrl}${path}`, fetchOptions);
        let payload;

        try {
            payload = await response.json();
        } catch (_error) {
            payload = {
                success: false,
                message: "Unable to parse server response.",
                data: {}
            };
        }

        if (!response.ok || payload.success === false) {
            const error = new Error(payload.message || "Request failed.");
            error.status = response.status;
            error.payload = payload;

            if (response.status === 401 && auth && !allowUnauthorized) {
                window.ZestMartUtils?.resetCurrentUser();
                window.location.href = "/";
            }

            throw error;
        }

        return payload;
    }

    window.ZestMartApi = {
        request,
        get(path, options) {
            return request(path, { ...(options || {}), method: "GET" });
        },
        post(path, body, options) {
            return request(path, { ...(options || {}), method: "POST", body });
        },
        put(path, body, options) {
            return request(path, { ...(options || {}), method: "PUT", body });
        },
        remove(path, options) {
            return request(path, { ...(options || {}), method: "DELETE" });
        }
    };
})();
