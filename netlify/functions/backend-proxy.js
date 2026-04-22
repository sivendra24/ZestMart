const TEXT_RESPONSE_TYPES = [
    "application/json",
    "application/javascript",
    "application/xml",
    "image/svg+xml",
    "text/",
];

const HOP_BY_HOP_HEADERS = new Set([
    "connection",
    "content-length",
    "host",
    "transfer-encoding",
]);

function normalizeBackendUrl() {
    const rawValue = process.env.ZESTMART_BACKEND_URL || "";
    return rawValue.trim().replace(/\/+$/, "");
}

function isTextResponse(contentType) {
    const normalized = (contentType || "").toLowerCase();
    return TEXT_RESPONSE_TYPES.some((prefix) => normalized.startsWith(prefix));
}

function getProxyPath(event) {
    const value = event.queryStringParameters?.path || "";
    return `/${value.replace(/^\/+/, "")}`;
}

function copyResponseHeaders(response) {
    const headers = {};

    response.headers.forEach((value, key) => {
        if (HOP_BY_HOP_HEADERS.has(key.toLowerCase())) {
            return;
        }
        headers[key] = value;
    });

    return headers;
}

exports.handler = async (event) => {
    const backendUrl = normalizeBackendUrl();
    if (!backendUrl) {
        return {
            statusCode: 503,
            headers: { "content-type": "application/json" },
            body: JSON.stringify({
                success: false,
                message: "ZESTMART_BACKEND_URL is not configured in Netlify.",
                data: {},
            }),
        };
    }

    const proxyPath = getProxyPath(event);
    const query = new URLSearchParams(event.queryStringParameters || {});
    query.delete("path");
    const targetUrl = `${backendUrl}${proxyPath}${query.toString() ? `?${query}` : ""}`;

    const requestHeaders = new Headers();
    Object.entries(event.headers || {}).forEach(([key, value]) => {
        if (!value || HOP_BY_HOP_HEADERS.has(key.toLowerCase())) {
            return;
        }
        requestHeaders.set(key, value);
    });

    const requestOptions = {
        method: event.httpMethod,
        headers: requestHeaders,
        redirect: "manual",
    };

    if (!["GET", "HEAD"].includes(event.httpMethod)) {
        requestOptions.body = event.isBase64Encoded
            ? Buffer.from(event.body || "", "base64")
            : event.body || "";
    }

    try {
        const response = await fetch(targetUrl, requestOptions);
        const headers = copyResponseHeaders(response);
        const contentType = response.headers.get("content-type") || "application/octet-stream";
        const arrayBuffer = await response.arrayBuffer();
        const buffer = Buffer.from(arrayBuffer);
        const textResponse = isTextResponse(contentType);

        return {
            statusCode: response.status,
            headers,
            body: textResponse ? buffer.toString("utf8") : buffer.toString("base64"),
            isBase64Encoded: !textResponse,
        };
    } catch (error) {
        return {
            statusCode: 502,
            headers: { "content-type": "application/json" },
            body: JSON.stringify({
                success: false,
                message: "Netlify could not reach the ZestMart backend.",
                data: { reason: error.message },
            }),
        };
    }
};
