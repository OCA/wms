import event_hub from "/shopfloor_mobile_base/static/wms/src/services/event_hub.js";

event_hub.$on("app.sync:update", (data) => {
    if (shopfloor_app_info.use_default_profile) {
        var profile = data.sync_data.data.user_info.default_profile;
        if (profile) {
            event_hub.$emit("profile:selected", profile);
        }
    }
});
