/**
 * Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simone.orsi@camptocamp.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {translation_registry} from "/shopfloor_mobile_base/static/wms/src/services/translation_registry.js";
import {
    AuthHandlerMixin,
    auth_handler_registry,
} from "/shopfloor_mobile_base/static/wms/src/services/auth_handler_registry.js";

// Provide auth handle for Odoo calls
export class UserAuthHandler extends AuthHandlerMixin {
    // Not sure we need anything if we get a cookie in the same browser
    get_params($root) {
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

    on_login($root, evt, data) {
        evt.preventDefault();
        // Call odoo application load => set the result in the local storage in json
        const odoo = $root.getOdoo({base_url: "/session/"});
        const def = $.Deferred();
        return odoo
            .post("auth/login", data, true)
            .then(function (response) {
                if (response.error) {
                    return def.reject();
                }
                return def.resolve();
            })
            .catch(function (error) {
                return def.reject();
            });
    }

    on_logout($root) {
        const def = $.Deferred();
        const odoo = $root.getOdoo({base_url: "/session/"});
        return odoo
            .post("auth/logout", null, true)
            .then(function () {
                return def.resolve();
            })
            .catch(function () {
                return def.reject();
            });
    }
}
auth_handler_registry.add(new UserAuthHandler("user"));

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
    },
    template: `
    <v-form v-on:submit="login">
        <v-text-field
            name="username"
            v-model="username"
            :label="$t('screen.login.username')"
            :placeholder="$t('screen.login.username')"
            autofocus
            autocomplete="off"></v-text-field>
        <v-text-field
            name="password"
            v-model="password"
            type="password"
            :label="$t('screen.login.password')"
            :placeholder="$t('screen.login.password')"
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

translation_registry.add("en-US.screen.login.username", "Username");
translation_registry.add("fr-FR.screen.login.username", "Nom d'utilisateur");
translation_registry.add("de-DE.screen.login.username", "Benutzername");

translation_registry.add("en-US.screen.login.password", "Password");
translation_registry.add("fr-FR.screen.login.password", "Mot de passe");
translation_registry.add("de-DE.screen.login.password", "Passwort");
