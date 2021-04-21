/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {page_registry} from "../services/page_registry.js";

export var SettingsControlPanel = Vue.component("settings-control-panel", {
    methods: {
        logout: function() {
            this.$root.logout();
        },
        get_pages: function() {
            return page_registry.by_tag("settings");
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
                        <btn-action @click="logout()">{{ $t('app.action.logout') }}</btn-action>
                    </v-col>
                </v-row>
                <v-row align="center">
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
        </Screen>
    `,
});
