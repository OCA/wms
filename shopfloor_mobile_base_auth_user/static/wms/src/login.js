/**
 * Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simone.orsi@camptocamp.com>
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
 */

import {translation_registry} from "/shopfloor_mobile_base/static/wms/src/services/translation_registry.js";
import {
    AuthHandlerMixin,
    auth_handler_registry,
} from "/shopfloor_mobile_base/static/wms/src/services/auth_handler_registry.js";

// Provide auth handle for Odoo calls
export class UserAuthHandler extends AuthHandlerMixin {
    get_params() {
        return {
            /**
             * NOTE: we don't have to provide any param because the auth
             * comes from the cookie.
             * In the future if we want to support cross domain
             * we'll have to provide `credentials` same-origin|include
             * to the fetch method.
             * */

            headers: {},
        };
    }

    get_login_component_name() {
        return "login-user";
    }

    on_login(data) {
        // Call odoo application load => set the result in the local storage in json
        const odoo = this.$root.getOdoo({base_url: "/session/"});
        return odoo
            .post("auth/login", data, true)
            .then(function (response) {
                if (response.error) {
                    return Promise.reject(response.error);
                }
                return response;
            })
            .catch(function (error) {
                return Promise.reject(error);
            });
    }

    on_logout() {
        const odoo = this.$root.getOdoo({base_url: "/session/"});
        return odoo.post("auth/logout", null, true);
    }
}
// Std user auth
auth_handler_registry.add("user", UserAuthHandler);
// Endpoint user auth (from endpoint_route_handler)
auth_handler_registry.add("user_endpoint", UserAuthHandler);

/**
 * Handle loging via user.
 *
 * Conventional name: `login-` + auth_type (from app config)
 */
Vue.component("login-user", {
    data: function () {
        return {
            username: "",
            password: "",
        };
    },
    methods: {
        login: function (evt) {
            const data = {login: this.username, password: this.password};
            this.$root.login(evt, data);
        },
        should_use_type_password: function () {
            // In some versions of iOS, using an input.type="password"
            // causes a bug with the device keyboard not showing,
            // which makes it impossible to introduce a password.
            // This has been observed in all iOS versions from 13 to 16.

            // For that reason, we need to use an input.type="text"
            // with a specific class that masks the characters
            // (thanks to CSS text-security).
            // However, this is not supported in Firefox.
            // Since Firefox doesn't have any known issues
            // with type="password", we still use it for that browser.
            return navigator.userAgent.includes("Firefox");
        },
    },
    template: `
    <v-form v-on:submit="login">
        <v-text-field
            name="username"
            v-model="username"
            :placeholder="$t('screen.login.username')"
            autofocus
            autocomplete="username"
        />
        <v-text-field
            name="password"
            v-model="password"
            :type="should_use_type_password() ? 'password' : 'text'"
            :class="should_use_type_password() ? '' : 'password-mask'"
            :placeholder="$t('screen.login.password')"
            autocomplete="current-password"
        />
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

translation_registry.add("en-US.screen.login.username", "Username");
translation_registry.add("fr-FR.screen.login.username", "Nom d'utilisateur");
translation_registry.add("de-DE.screen.login.username", "Benutzername");

translation_registry.add("en-US.screen.login.password", "Password");
translation_registry.add("fr-FR.screen.login.password", "Mot de passe");
translation_registry.add("de-DE.screen.login.password", "Passwort");
