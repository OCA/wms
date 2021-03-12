/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */
import {page_registry} from "../services/page_registry.js";

export var Language = {
    template: `
        <Screen :screen_info="{title: $t('screen.settings.language.title'), klass: 'settings settings-language'}">
            <manual-select
                :records="available_languages"
                :options="{initValue: active_language_code, showActions: false}"
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
};

page_registry.add(
    "language",
    Language,
    {},
    {
        tag: "settings",
        icon: "mdi-flag",
        display_name: function(instance, rec) {
            return [
                instance.$t("screen.settings.language.name"),
                instance.active_language,
            ].join(" - ");
        },
    }
);

export default Language;
