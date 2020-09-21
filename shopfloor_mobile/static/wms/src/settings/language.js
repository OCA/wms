/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

export var Language = Vue.component("language", {
    template: `
        <Screen :screen_info="{title: $t('screen.settings.language.title'), klass: 'settings settings-language'}">
            <manual-select
                :records="available_languages"
                :options="{initValue: current_language_code, showActions: false}"
                v-on:select="on_select"
                />

            <div class="button-list button-vertical-list full">
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <btn-back/>
                    </v-col>
                </v-row>
            </div>
        </Screen>
    `,
    methods: {
        on_select: function(selected) {
            const self = this;
            this.$i18n.locale = selected.id;
            // this.$root.trigger("language:selected", selected, true);
            self.$root.$router.push({name: "home"});
        },
    },
    computed: {
        available_languages() {
            // FIXME: this should come from odoo and from app config
            // They will match w/ $i18n.availableLocales
            return [
                {
                    id: "en-US",
                    name: this.$t("language.name.English"),
                },
                {
                    id: "fr-FR",
                    name: this.$t("language.name.French"),
                },
                {
                    id: "de-DE",
                    name: this.$t("language.name.German"),
                },
            ];
        },
        current_language_code() {
            return this.$i18n.locale || "en-US";
        },
    },
});
