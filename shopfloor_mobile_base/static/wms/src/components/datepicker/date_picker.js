/**
 * Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
 * License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
 */

export var DatePicker = Vue.component("date-picker-input", {
    data: function () {
        return {
            date: "",
        };
    },
    computed: {
        userLocale: function () {
            const lang = this.$root.user?.lang || "en-US";
            // Vuetify works with kebab-case (en-us instead of en_US)
            return lang.replace("_", "-").toLowerCase();
        },
    },
    template: `
    <v-menu
        transition="scale-transition"
        offset-y
        min-width="auto"
    >
        <template v-slot:activator="{ on, attrs }">
            <v-text-field
                label="Select expiry date"
                readonly
                prepend-icon="mdi-calendar"
                v-model="date"
                v-bind="attrs"
                v-on="on"
            />
        </template>
        <v-date-picker
            v-model="date"
            @change="$emit('dateChange', date)"
            :locale="userLocale"
        />
    </v-menu>
    `,
});
