/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

export var SettingsControlPanel = Vue.component("settings-control-panel", {
    data: function() {
        return {
            profile_name: this.$root.has_profile ? this.$root.profile.name : "?",
            workstation_name: this.$root.workstation
                ? this.$root.workstation.name
                : "?",
        };
    },
    methods: {
        logout: function() {
            this.$root.logout();
        },
    },
    computed: {
        available_languages() {
            return this.$root.available_languages;
        },
        active_language() {
            const language = this.available_languages.find(
                ({id}) => id === this.$i18n.locale
            );
            return language ? language.name : "?";
        },
    },
    template: `
        <Screen :screen_info="{title: $t('screen.settings.home.title'), klass: 'settings settings-control-panel'}">

            <v-card outlined v-if="$root.user.id">
                <v-list>
                    <v-list-item>
                        <v-list-item-avatar>
                            <v-avatar color="primary" size="36">
                                <v-icon dark>mdi-account-circle</v-icon>
                            </v-avatar>
                        </v-list-item-avatar>
                        <v-list-item-content>
                            <span v-text="$root.user.name" />
                        </v-list-item-content>
                    </v-list-item>
                </v-list>
            </v-card>
            <div class="button-list button-vertical-list full">
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <v-btn @click="$router.push({'name': 'profile'})">
                            <v-icon>mdi-account-cog</v-icon>
                            <span>{{ $t("screen.settings.profile.name") }} - {{ profile_name }}</span>
                        </v-btn>
                    </v-col>
                </v-row>
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <v-btn @click="$router.push({'name': 'workstation'})">
                            <v-icon>mdi-printer</v-icon>
                            <span>{{ $t("screen.settings.workstation.name") }} - {{ workstation_name }}</span>
                        </v-btn>
                    </v-col>
                </v-row>
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <v-btn @click="$router.push({'name': 'language'})">
                            <v-icon>mdi-flag</v-icon>
                            <span>{{ $t("screen.settings.language.name") }} - {{ this.active_language }}</span>
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
