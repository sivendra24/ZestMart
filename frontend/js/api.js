(function () {
    const config = window.ZestMartConfig;
    const demoApi = window.ZestMartDemoApi;

    async function requestViaDemo(path, options) {
        if (!demoApi?.isEnabled()) {
            throw new Error("Demo mode is not available.");
        }
        return demoApi.request(path, options || {});
    }

    function buildRequestOptions(options) {
        const {
            method = "GET",
            body,
            auth = false,
            allowUnauthorized = false,
            formData = false,
            headers = {}
        } = options || {};

        return {
            method,
            body,
            auth,
            allowUnauthorized,
            formData,
            headers,
        };
    }

    function shouldTryAnotherBase(response, payload) {
        if (!response) {
            return true;
        }
        if (response.status === 404) {
            return true;
        }
        if (response.status === 502 || response.status === 503) {
            return true;
        }
        if (!response.ok && payload?.message === "Unable to parse server response.") {
            return true;
        }
        return false;
    }

    async function request(path, options) {
        const requestOptions = buildRequestOptions(options);
        const {
            method,
            body,
            auth,
            allowUnauthorized,
            formData,
            headers,
        } = requestOptions;

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

        if (demoApi?.isActive()) {
            return requestViaDemo(path, requestOptions);
        }

        let lastParsedPayload = null;
        const apiBaseUrls = config.apiBaseUrls || [window.location.origin];
        for (const apiBaseUrl of apiBaseUrls) {
            let response;
            try {
                response = await fetch(`${apiBaseUrl}${path}`, fetchOptions);
            } catch (networkError) {
                if (apiBaseUrl !== apiBaseUrls[apiBaseUrls.length - 1]) {
                    continue;
                }
                if (demoApi?.isEnabled()) {
                    return requestViaDemo(path, requestOptions);
                }
                throw networkError;
            }

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

            lastParsedPayload = payload;

            if (shouldTryAnotherBase(response, payload) && apiBaseUrl !== apiBaseUrls[apiBaseUrls.length - 1]) {
                continue;
            }

            if ((response.status === 502 || response.status === 503) && demoApi?.isEnabled()) {
                return requestViaDemo(path, requestOptions);
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

        if (demoApi?.isEnabled()) {
            return requestViaDemo(path, requestOptions);
        }

        const error = new Error(lastParsedPayload?.message || "Request failed.");
        error.payload = lastParsedPayload;
        throw error;
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
