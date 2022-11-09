/**
 * Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
 * License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
 */

import event_hub from "../../services/event_hub.js";

export var DatePicker = Vue.component("date-picker-input", {
    data: function () {
        return {
            date: "",
        };
    },
    watch: {
        date: function () {
            this.$root.trigger("date_picker_selected", this.date);
        },
    },
    mounted() {
        event_hub.$on("datepicker:lotselected", (lot) => {
            if (!lot.expiration_date) {
                return;
            }
            this.date = lot.expiration_date.split("T")[0];
        });
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
                ></v-text-field>
            </template>
            <v-date-picker
                v-model="date"
            ></v-date-picker>
        </v-menu>
    `,
});
