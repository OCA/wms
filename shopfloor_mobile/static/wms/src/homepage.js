/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Thierry Ducrest <thierry.ducrest@camptocamp.com>
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */
import {demotools} from "./demo/demo.core.js";

export var HomePage = Vue.component("home-page", {
    computed: {
        navigation() {
            return this.$root.appmenu.menus;
        },
    },
    methods: {
        nuke_data_and_reload: function() {
            if (!this.$root.demo_mode) {
                return;
            }
            // Force reload config (loads profiles)
            this.$root._clearConfig();
            // Enforce 1st profile
            const selected_profile = _.head(demotools.makeProfiles());
            this.$root.trigger("profile:selected", selected_profile, true);
            // Reload page
            location.reload();
        },
    },
    props: ["routes"],
    template: `
        <Screen :screen_info="{title: $t('screen.home.main_title'), klass: 'home'}" :show-menu="false">
            <v-list v-if="$root.has_profile">
                <nav-items :navigation="navigation"/>
            </v-list>

            <v-alert tile class="mt10" color="warning" v-if="$root.demo_mode">DEMO MODE ON</v-alert>
            <div class="button-list button-vertical-list full" v-if="$root.demo_mode">
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <btn-action action="cancel" @click="nuke_data_and_reload()">{{ $t('screen.home.action.nuke_data_and_reload') }}</btn-action>
                    </v-col>
                </v-row>
            </div>

            <v-footer absolute padless>
                <v-col class="text-center font-weight-light" cols="12">
                    <span class="version">{{ $t('screen.home.version') }}</span> <span class="version-number" v-text="$root.app_info.app_version" />
                </v-col>
            </v-footer>
        </Screen>
    `,
});
