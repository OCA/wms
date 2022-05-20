export default (data) => {
    _.defaults(data, {
        running_env: "dev",
        is_authenticated: true,
    });
    return {
        // Can't mock private methods starting with _
        app_info: {
            running_env: data.running_env,
        },
        is_authenticated: () => data.is_authenticated,
    };
};
