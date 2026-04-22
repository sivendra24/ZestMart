(() => {
    const hostname = window.location.hostname;
    const isLocalHost = hostname === "localhost" || hostname === "127.0.0.1";

    window.ZestMartConfig = {
        apiBaseUrls: isLocalHost
            ? [window.location.origin]
            : [window.location.origin, `${window.location.origin}/api`],
        allowDemoFallback: !isLocalHost,
        routes: {
            student: "/student",
            delivery: "/delivery",
            admin: "/admin"
        }
    };
})();
