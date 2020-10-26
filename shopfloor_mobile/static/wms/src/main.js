/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Raphaël Reverdy <raphael.reverdy@akretion.com>
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {router} from "./router.js";
import {i18n} from "./i18n.js";
import {GlobalMixin} from "./mixin.js";
import {process_registry} from "./services/process_registry.js";
import {color_registry} from "./services/color_registry.js";
import {Odoo, OdooMocked} from "./services/odoo.js";
import VueSuperMethod from "./lib/vue-super-call.js";

Vue.prototype.$super = VueSuperMethod;

// TODO: we need a local storage handler too, to store device/profile specific data
Vue.use(Vue2Storage, {
    prefix: "shopfloor_",
    driver: "session", // local|session|memory
    ttl: 60 * 60 * 24 * 1000, // 24 hours
});

Vue.use(Vuetify);

var EventHub = new Vue();

Vue.mixin(GlobalMixin);

let app_components = {};
_.forEach(process_registry.all(), function(process, key) {
    app_components[process.key] = process.component;
});
if (app_components.length)
    console.log("Registered component:", app_components.join(", "));

const app = new Vue({
    i18n,
    router: router,
    vuetify: new Vuetify({
        theme: {
            themes: color_registry.get_themes(),
        },
    }),
    components: app_components,
    data: function() {
        return {
            demo_mode: false,
            global_state_key: "",
            // collect global events
            event_hub: EventHub,
            current_profile: {},
            profile_menu: null,
            current_apikey: null,
            loading: false,
            appconfig: null,
            authenticated: false,
            registry: process_registry,
        };
    },
    created: function() {
        const self = this;
        this.demo_mode = this.app_info.demo_mode;
        this.loadConfig();
        document.addEventListener("fetchStart", function() {
            self.loading = true;
        });
        document.addEventListener("fetchEnd", function() {
            self.loading = false;
        });
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
            self.loadMenu(true);
        });
    },
    computed: {
        app_info: function() {
            return shopfloor_app_info;
        },
        has_profile: function() {
            return !_.isEmpty(this.profile);
        },
        // TODO: we can add an handler for this and avoid duplicate code
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
        profiles: function() {
            return this.appconfig ? this.appconfig.profiles || [] : [];
        },
        appmenu: {
            get: function() {
                if (_.isEmpty(this.profile_menu)) {
                    this.profile_menu = this.$storage.get("menu");
                }
                return this.profile_menu || [];
            },
            set: function(v) {
                this.profile_menu = v;
                this.$storage.set("menu", v);
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
        loadConfig: function(force) {
            if (this.appconfig && !force) {
                return this.appconfig;
            }
            // TODO: we can do this via watcher
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
        _loadConfig: function() {
            const self = this;
            const odoo = self.getOdoo({usage: "app"});
            return odoo.call("user_config").then(function(result) {
                if (!_.isUndefined(result.data)) {
                    self.appconfig = result.data;
                    self.authenticated = true;
                    self.$storage.set("appconfig", self.appconfig);
                } else {
                    // TODO: any better thing to do here?
                    console.log(result);
                }
            });
        },
        _clearConfig: function(reload = true) {
            this.$storage.remove("appconfig");
            if (reload) return this._loadConfig();
        },
        _clearAppData: function() {
            this.apikey = "";
            this.appmenu = [];
            this.profile = null;
            this._clearConfig(false);
        },
        loadMenu: function(force) {
            if (this.appmenu && !force) {
                return this.appmenu;
            }
            this._loadMenu();
            return this.appmenu;
        },
        _loadMenu: function() {
            const self = this;
            const odoo = self.getOdoo({
                usage: "user",
                profile_id: this.profile.id,
            });
            return odoo.call("menu").then(function(result) {
                self.appmenu = result.data;
            });
        },
        logout: function() {
            this.authenticated = false;
            this._clearAppData();
            this.$router.push({name: "login"});
        },
        // Likely not needed anymore
        loadJS: function(url, script_id) {
            if (script_id && !document.getElementById(script_id)) {
                console.debug("Load JS", url);
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
        trigger(event_name, data, no_state) {
            if (this.global_state_key && !no_state) {
                event_name = this.global_state_key + ":" + event_name;
            }
            this.event_hub.$emit(event_name, data);
        },
    },
}).$mount("#app");
