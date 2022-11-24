/**
 * Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
 * License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
 */

import event_hub from "../../services/event_hub.js";

export var DatePicker = Vue.component("date-picker-input", {
    props: {
        // Method passed from the parent to update the picker's date
        // from outside as required.
        handler_to_update_date: Function,
    },
    data: function () {
        return {
            date: "",
        };
    },
    watch: {
        date: function () {
            this.$emit("date_picker_selected", this.date);
        },
    },
    mounted() {
        event_hub.$on("datepicker:newdate", (data) => {
            this.date = this.handler_to_update_date(data);
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
