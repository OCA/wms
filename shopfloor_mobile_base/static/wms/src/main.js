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
import {config_registry} from "./services/config_registry.js";
import {process_registry} from "./services/process_registry.js";
import {page_registry} from "./services/page_registry.js";
import {color_registry} from "./services/color_registry.js";
import {Odoo, OdooMocked} from "./services/odoo.js";
import VueSuperMethod from "./lib/vue-super-call.js";

Vue.prototype.$super = VueSuperMethod;

// TODO: we need a local storage handler too, to store device/profile specific data
// Maybe replace w/ https://github.com/ankurk91/vue-web-storage
Vue.use(Vue2Storage, {
    prefix: "shopfloor_",
    driver: "session", // local|session|memory
    ttl: 60 * 60 * 24 * 1000, // 24 hours
});

Vue.use(Vuetify);

var EventHub = new Vue();

Vue.mixin(GlobalMixin);

let APP_COMPONENTS = {};

const register_app_components = function(components) {
    _.forEach(components, function(process, key) {
        APP_COMPONENTS[process.key] = process.component;
    });
    if (APP_COMPONENTS.length)
        console.log("Registered component:", APP_COMPONENTS.join(", "));
};

register_app_components(process_registry.all());
register_app_components(page_registry.all());

config_registry.add("apikey", {default: "", reset_on_clear: true});
config_registry.add("profile", {default: {}, reset_on_clear: true});
config_registry.add("appmenu", {default: [], reset_on_clear: true});
config_registry.add("authenticated", {default: false, reset_on_clear: true});

const app = new Vue({
    i18n,
    router: router,
    vuetify: new Vuetify({
        theme: {
            themes: color_registry.get_themes(),
        },
    }),
    components: APP_COMPONENTS,
    data: function() {
        let data = {
            demo_mode: false,
            global_state_key: "",
            // collect global events
            event_hub: EventHub,
            loading: false,
            appconfig: null,
        };
        _.merge(data, config_registry.generare_data_keys());
        return data;
    },
    beforeCreate: function() {
        config_registry._set_root(this);
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
        ...config_registry.generate_computed_properties(),
        app_info: function() {
            return shopfloor_app_info;
        },
        available_languages: function() {
            // FIXME: this should come from odoo and from app config
            // They will match w/ $i18n.availableLocales
            return [
                {
                    id: "en-US",
                    name: this.$t("language.name.English"),
                },
                {
                    id: "fr-FR",
                    name: this.$t("language.name.French"),
                },
                {
                    id: "de-DE",
                    name: this.$t("language.name.German"),
                },
            ];
        },
        has_profile: function() {
            return !_.isEmpty(this.profile);
        },
        profiles: function() {
            return this.appconfig ? this.appconfig.profiles || [] : [];
        },
        user: function() {
            return this.appconfig ? this.appconfig.user_info || {} : {};
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
            config_registry.reset_on_clear();
            this._clearConfig(false);
        },
        loadMenu: function(force) {
            if ((this.appmenu && !force) || !this.has_profile) {
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
        getNav: function() {
            return _.result(this, "appmenu.menus", []);
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
