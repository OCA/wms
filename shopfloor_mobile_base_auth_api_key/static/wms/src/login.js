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
        login: function (evt) {
            this.$root.apikey = this.apikey;
            this.$root.login(evt);
        },
    },
    template: `
    <v-form v-on:submit="login">
        <v-text-field
            name="apikey"
            v-model="apikey"
            :label="$t('screen.login.api_key_label')"
            :placeholder="$t('screen.login.api_key_placeholder')"
            autofocus
            autocomplete="off"></v-text-field>
        <div class="button-list button-vertical-list full">
            <v-row align="center">
                <v-col class="text-center" cols="12">
                    <v-btn color="success" type="submit">{{ $t('screen.login.action.login') }}</v-btn>
                </v-col>
            </v-row>
        </div>
    </v-form>
    `,
});

translation_registry.add("en-US.screen.login.api_key_label", "API key");
translation_registry.add("fr-FR.screen.login.api_key_label", "Clé API");
translation_registry.add("de-DE.screen.login.api_key_label", "API-Schlüssel");

translation_registry.add("en-US.screen.login.api_key_placeholder", "YOUR_API_KEY_HERE");
translation_registry.add("fr-FR.screen.login.api_key_placeholder", "VOTRE_CLE_API_ICI");
translation_registry.add(
    "de-DE.screen.login.api_key_placeholder",
    "DEIN_API-SCHLÜSSEL_HIER"
);
