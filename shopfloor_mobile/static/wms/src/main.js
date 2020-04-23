import {router} from "./router.js";
import {Config} from "./services/config.js";
import {process_registry} from "./services/process_registry.js";
import {Odoo, OdooMocked} from "./services/odoo.js";

Vue.use(Vue2Storage, {
    prefix: "shopfloor_",
    driver: "session", // local|session|memory
    ttl: 60 * 60 * 24 * 1000, // 24 hours
});

var EventHub = new Vue();

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
            global_state_key: "",
            // collect global events
            event_hub: EventHub,
            current_profile: {},
            current_apikey: null,
            loading: false,
            appconfig: null,
            authenticated: false,
            registry: process_registry,
        };
    },
    created: function() {
        this.demo_mode = window.location.pathname.includes("demo");
        if (this.demo_mode) {
            this.loadJS("src/demo/demo.core.js", "demo_core");
        }
        this.loadConfig();
    },
    mounted: function() {
        const self = this;
        // components can trigger `state:change` on the root
        // and the current state gets stored into `global_state_key`
        this.$root.$on("state:change", function(key) {
            self.global_state_key = key;
        });
        this.$root.event_hub.$on("profile:selected", function(profile) {
            self.profile = profile;
        });
        if (this.authenticated) {
            // TODO: this should be done by a watcher on appconfig change
            this._loadRoutes();
        }
    },
    computed: {
        has_profile: function() {
            return !_.isEmpty(this.profile);
        },
        profile: {
            get: function() {
                if (_.isEmpty(this.current_profile)) {
                    this.current_profile = this.$storage.get("profile");
                }
                return this.current_profile;
            },
            set: function(v) {
                this.current_profile = v;
                this.$storage.set("profile", v);
            },
        },
        apikey: {
            get: function() {
                if (!this.current_apikey) {
                    this.current_apikey = this.$storage.get("apikey");
                }
                return this.current_apikey;
            },
            set: function(v) {
                this.current_apikey = v;
                this.$storage.set("apikey", v);
            },
        },
    },
    methods: {
        getOdoo: function(odoo_params) {
            const params = _.defaults({}, odoo_params, {
                apikey: this.apikey,
                debug: this.demo_mode,
            });
            let OdooClass;
            if (this.demo_mode) {
                OdooClass = OdooMocked;
            } else {
                OdooClass = Odoo;
            }
            return new OdooClass(params);
        },
        loadConfig: function() {
            if (this.appconfig) {
                return this.appconfig;
            }
            const stored = this.$storage.get("appconfig");
            if (stored) {
                this.appconfig = stored;
                // Storage is by session, hence we assume we are authenticated.
                // TODO: any better way?
                this.authenticated = true;
                return this.appconfig;
            }
            this._loadConfig();
        },
        _loadConfig: function(odoo_params) {
            const self = this;
            self.loading = true;
            const odoo = self.getOdoo({usage: "app"});
            const config = new Config(odoo);
            return config.load().then(function() {
                if (config.authenticated) {
                    self.appconfig = config.data;
                    self.authenticated = config.authenticated;
                    self.$storage.set("appconfig", self.appconfig);
                    self.loading = false;
                }
            });
        },
        _loadRoutes: function() {
            const self = this;
            // Adding the routes dynamically when received from ther server
            self.appconfig.menus.forEach(function(item) {
                const registered = self.registry.get(item.process.code);
                if (registered) {
                    self.$router.addRoutes([
                        {
                            path: self.registry.make_route(item.process.code),
                            component: self.registry.get(item.process.code),
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
            // TODO: any better way to do it?
            // As we load routes on demand the router does not know it yet,
            // Hence we have to force the switch.
            // hash is smth like "#/checkout/12"
            self.$router.push({path: window.location.hash.replace("#/", "")});
        },
        _clearConfig: function() {
            this.$storage.remove("appconfig");
            return this._loadConfig();
        },
        logout: function() {
            this.apikey = "";
            this.authenticated = false;
            this.$router.push({name: "login"});
        },
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
