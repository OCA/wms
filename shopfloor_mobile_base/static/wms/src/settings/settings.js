/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
 */

import {page_registry} from "../services/page_registry.js";

export var SettingsControlPanel = Vue.component("settings-control-panel", {
    methods: {
        logout: function () {
            this.$root.logout();
        },
        get_pages: function () {
            const self = this;
            return page_registry.by_tag("settings").filter(function (page) {
                return page.metadata.is_enabled(self, page);
            });
        },
        _loadEruda: function () {
            return new Promise((resolve, reject) => {
                if (typeof eruda !== "undefined") {
                    return resolve(window.eruda);
                }

                const script = document.createElement("script");
                script.src =
                    "/shopfloor_mobile_base/static/wms/src/lib/eruda/eruda-v3.4.3.min.js";
                script.id = "script_eruda";

                script.onload = () => {
                    resolve(window.eruda);
                };
                script.onerror = () => {
                    console.error("Impossible to load Eruda devtools.");
                    reject(new Error("Failed to load Eruda"));
                };

                document.head.appendChild(script);
            });
        },
        toggleDevTools: async function () {
            try {
                await this._loadEruda();
            } catch (e) {
                return;
            }

            const isErudaActive = !!this.$storage.get("eruda_active", false);

            if (!isErudaActive || !eruda._isInit) {
                eruda.init();
                this.$storage.set("eruda_active", true);
            } else {
                eruda.destroy();
                this.$storage.set("eruda_active", false);
            }
        },
    },
    template: `
        <Screen :screen_info="{title: $t('screen.settings.home.title'), klass: 'settings settings-control-panel'}">
            <v-card outlined v-if="$root.user.id">
                <user-session-detail :show_profile="false" />
            </v-card>
            <div class="button-list button-vertical-list full">
                <v-row align="center" v-for="page in get_pages()" :key="make_component_key([page.key])">
                    <v-col class="text-center" cols="12">
                        <v-btn @click="$router.push({'name': page.key})" :data-action="'setting-' + page.key">
                            <v-icon v-text="page.metadata.icon || 'mdi-account-cog'"/>
                            <span>{{ page.metadata.display_name(_self, page) }}</span>
                        </v-btn>
                    </v-col>
                </v-row>
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <v-btn @click="toggleDevTools()">
                            <v-icon left>mdi-bug</v-icon>
                            {{ $t('app.action.toggle_devtools') || 'Toggle DevTools' }}
                        </v-btn>
                    </v-col>
                </v-row>
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <btn-action color="primary" @click="logout()">{{ $t('app.action.logout') }}</btn-action>
                    </v-col>
                </v-row>
                <v-row align="center" v-if="app_options.show_fullscreen_btn">
                    <v-col class="text-center" cols="12">
                        <btn-fullscreen />
                    </v-col>
                </v-row>
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <btn-back/>
                    </v-col>
                </v-row>
            </div>
            <app-version-footer/>
        </Screen>
    `,
});
