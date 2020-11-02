/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Raphaël Reverdy <raphael.reverdy@akretion.com>
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Thierry Ducrest <thierry.ducrest@camptocamp.com>
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */
export var LoginPage = Vue.component("login-page", {
    data: function() {
        return {
            apikey: "",
            error: "",
        };
    },
    computed: {
        screen_info: function() {
            return {
                title: this.$t("screen.login.title"),
                klass: "login",
                user_message: this.user_message,
                noUserMessage: !this.error,
                showMenu: false,
            };
        },
        user_message: function() {
            return {body: this.error, message_type: "error"};
        },
    },
    methods: {
        login: function(evt) {
            evt.preventDefault();
            // Call odoo application load => set the result in the local storage in json
            this.error = "";
            this.$root.apikey = this.apikey;
            this.$root
                ._loadConfig()
                .catch(error => {
                    this._handle_invalid_key();
                })
                .then(() => {
                    // TODO: shall we do this in $root._loadRoutes?
                    if (this.$root.authenticated) {
                        this.$router.push({name: "home"});
                    } else {
                        this._handle_invalid_key();
                    }
                });
        },
        _handle_invalid_key() {
            this.error = this.$("screen.login.error.api_key_invalid");
            this.$root.apikey = "";
        },
    },
    template: `
    <Screen :screen_info="screen_info" :show-menu="false">
        <v-container>
            <v-row
                align="center"
                justify="center">
                <v-col cols="12" sm="8" md="4">
                    <div class="login-wrapper">
                        <v-form v-on:submit="login">
                            <v-text-field
                                v-model="apikey"
                                label="API Key"
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
                    </div>
                </v-col>
            </v-row>
            <div class="button-list button-vertical-list full">
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <btn-fullscreen />
                    </v-col>
                </v-row>
            </div>
        </v-container>
    </Screen>
    `,
});
