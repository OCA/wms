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
        />
    </v-menu>
    `,
});
