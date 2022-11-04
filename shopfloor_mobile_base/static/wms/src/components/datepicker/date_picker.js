/**
 * Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
 * License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
 */

export var DatePicker = Vue.component("date-picker-input", {
    data: function () {
        return {
            expiry_date: "",
        };
    },
    watch: {
        expiry_date: function () {
            this.$root.trigger("date_picker_selected", this.expiry_date);
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
                v-model="expiry_date"
                v-bind="attrs"
                v-on="on"
            ></v-text-field>
        </template>
        <v-date-picker
            v-model="expiry_date"
        ></v-date-picker>
    </v-menu>
    `,
});
