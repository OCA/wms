/**
 * @author Simone Orsi <simone.orsi@camptocamp.com>
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
 */

import {translation_registry} from "/shopfloor_mobile_base/static/wms/src/services/translation_registry.js";
import {
    AuthHandlerMixin,
    auth_handler_registry,
} from "/shopfloor_mobile_base/static/wms/src/services/auth_handler_registry.js";
import {config_registry} from "/shopfloor_mobile_base/static/wms/src/services/config_registry.js";

//  Register apikey storage
config_registry.add("apikey", {default: "", reset_on_clear: true});

// Provide auth handle for Odoo calls
export class ApiKeyAuthHandler extends AuthHandlerMixin {
    get_params() {
        return {
            headers: {
                "API-KEY": this.$root.apikey,
            },
        };
    }

    // on_login($root, evt, data) {
    // No need for a handler as we set the api_key inside the login method
    // }

    // on_logout($root) {
    // No need for a handler as the reset_on_clear flag in the config_registry
    // is going to flush the api_key on appdata cleanup
    // }
}

auth_handler_registry.add("api_key", ApiKeyAuthHandler);

/**
 * Handle loging via API key.
 *
 * Conventional name: `login-` + auth_type (from app config)
 */
Vue.component("login-api_key", {
    data: function () {
        return {
            apikey: "",
        };
    },
    methods: {
        login: function (apikey) {
            this.$root.apikey = apikey.text;
            this.$root.login();
        },
    },
    template: `
    <div class="text-center"">
        <searchbar
            v-on:found="login"
            :input_label="$t('screen.login.api_key_label')"
            :input_placeholder="$t('screen.login.api_key_placeholder')"
            forcefocus
            input_type="password"/>
    </div>
    `,
});

translation_registry.add("en-US.screen.login.api_key_label", "API key");
translation_registry.add("fr-FR.screen.login.api_key_label", "Clé API");
translation_registry.add("de-DE.screen.login.api_key_label", "API-Schlüssel");

translation_registry.add("en-US.screen.login.api_key_placeholder", "Scan your badge");
translation_registry.add(
    "fr-FR.screen.login.api_key_placeholder",
    "Scannez votre badge"
);
translation_registry.add(
    "de-DE.screen.login.api_key_placeholder",
    "Scannen Sie Ihr Abzeichen"
);
