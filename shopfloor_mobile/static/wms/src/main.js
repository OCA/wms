import {router} from "./router.js";
import {Config} from "./services/config.js";
import {Storage} from "./services/storage.js";
import {process_registry} from "./services/process_registry.js";

var EventHub = new Vue();

var AppConfig = new Config();

if (Storage.apikey) {
    AppConfig.load().then(() => {
        // Adding the routes dynamically when received from ther server
        AppConfig.get("menus").forEach(function(item) {
            const registered = process_registry.get(item.process.code);
            if (registered) {
                app.$router.addRoutes([
                    {
                        path: "/" + item.process.code,
                        component: process_registry.get(item.process.code),
                        props: {menuItem: item},
                    },
                ]);
            } else {
                // TODO: use NotFound component
                console.error(
                    "Cannot find process component for",
                    item.process.code,
                    item
                );
            }
        });
    });
}

const vuetify_themes = {
    light: {
        primary: "#491966",
        secondary: "#424242",
        accent: "#82B1FF",
        error: "#FF5252",
        info: "#2196F3",
        success: "#4CAF50",
        warning: "#FFC107",
    },
};

const app = new Vue({
    router: router,
    vuetify: new Vuetify({
        // FIXME: has no effect
        // theme: {
        //     themes: vuetify_themes
        // }
    }),
    data: function() {
        return {
            demo_mode: false,
            config: AppConfig,
            global_state_key: "",
            // collect global events
            event_hub: EventHub,
            current_profile: {},
        };
    },
    created: function() {
        this.demo_mode = window.location.pathname.includes("demo");
        if (this.demo_mode) {
            this.loadJS("src/demo/demo.core.js", "demo_core");
        }
    },
    mounted: function() {
        const self = this;
        // components can trigger `state:change` on the root
        // and the current state gets stored into `global_state_key`
        this.$root.$on("state:change", function(key) {
            self.global_state_key = key;
        });
        this.$root.event_hub.$on("profile:selected", function(profile) {
            self.current_profile = profile;
        });
    },
    computed: {
        profile: function() {
            // TODO: retrieve profile from session.
            // ATM we always have to trigger the selection to set it.
            return this.current_profile;
        },
    },
    methods: {
        loadJS: function(url, script_id) {
            if (script_id && !document.getElementById(script_id)) {
                console.log("Load JS", url);
                var script = document.createElement("script");
                script.setAttribute("src", url);
                script.setAttribute("type", "module");
                script.setAttribute("id", script_id);
                document.getElementsByTagName("head")[0].appendChild(script);
            }
        },
        /*
        Trigger and event on the event hub.
        If a state is available, prefix event name w/ it.
        Components using our mixin for state machine can define events
        on each state using `events` array. See mixin for details.
        Components can use `$root.trigger(...)` to trigger and event on the hub.
        */
        trigger(event_name, data) {
            if (this.global_state_key) {
                event_name = this.global_state_key + ":" + event_name;
            }
            this.event_hub.$emit(event_name, data);
        },
    },
}).$mount("#app");
