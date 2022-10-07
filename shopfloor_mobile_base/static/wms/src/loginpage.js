/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Raphaël Reverdy <raphael.reverdy@akretion.com>
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Thierry Ducrest <thierry.ducrest@camptocamp.com>
 * @author Simone Orsi <simahawk@gmail.com>
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
 */
import event_hub from "./services/event_hub.js";

export var LoginPage = Vue.component("login-page", {
    data: function () {
        return {
            error: "",
        };
    },
    beforeCreate: function () {
        const self = this;
        if (this.$root.is_authenticated()) {
            self.$router.push("/");
        }
    },
    mounted: function () {
        const self = this;
        event_hub.$once("login:before", function () {
            self.error = "";
        });
        event_hub.$once("login:success", function () {
            const home_route = self.$router.options.routes.find((route) => {
                // isHomeRoute can be set on route registration to use
                // any custom route as home;
                // if no route is explicitly set as home
                // the router will use a default.
                return route.meta ? route.meta.isHomeRoute : false;
            });
            self.$router.push({name: home_route.name});
        });
        event_hub.$once("login:failure", function () {
            self._handle_invalid_login();
        });
    },
    computed: {
        screen_info: function () {
            return {
                title: this.$t("screen.login.title"),
                klass: "login",
                user_message: this.user_message,
                noUserMessage: !this.error,
                showMenu: false,
            };
        },
        user_message: function () {
            return {body: this.error, message_type: "error"};
        },
    },
    methods: {
        login_form_component_name() {
            const auth_handler = this.$root._get_auth_handler();
            return auth_handler.get_login_component_name();
        },
        _handle_invalid_login() {
            this.error = this.$root.$t("screen.login.error.login_invalid");
        },
    },
    template: `
    <Screen :screen_info="screen_info" :show-menu="false">
        <v-container>
            <v-row align="center" v-if="$root.app_info.running_env != 'prod'">
                <v-col cols="12">
                    <v-alert
                        dense
                        colored-border
                        type="warning"
                        border="left"
                        elevation="2"
                        :icon="false"
                        >
                        <user-session-detail :show_profile="false" :show_user="false" :show_report_issue_action="false" />
                    </v-alert>
                </v-col>
            </v-row>
            <v-row
                align="center"
                justify="center">
                <v-col cols="12" sm="8" md="4">
                    <div class="login-wrapper">
                        <component
                            :is="login_form_component_name()"
                            />
                    </div>
                </v-col>
            </v-row>
            <div class="button-list button-vertical-list full" v-if="app_options.show_fullscreen_btn">
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <btn-fullscreen />
                    </v-col>
                </v-row>
            </div>
            <div class="button-list button-vertical-list full">
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <report-issue-action display_mode="inline" />
                    </v-col>
                </v-row>
            </div>
        </v-container>
    </Screen>
    `,
});
