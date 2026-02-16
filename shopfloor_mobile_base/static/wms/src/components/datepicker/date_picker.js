/**
 * Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
 * License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
 */

export var DatePicker = Vue.component("date-picker-input", {
    data: function () {
        return {
            date: "",

            // Control menu state manually to prevent closing during month/year navigation.
            menu: false,
        };
    },
    computed: {
        userLocale: function () {
            const lang = this.$root.user?.lang || "en-US";
            return lang.replace("_", "-").toLowerCase();
        },
    },
    methods: {
        onDateChange(newDate) {
            this.menu = false;
            this.$emit("dateChange", newDate);
        },
    },
    template: `
    <v-menu
        v-model="menu"
        :close-on-content-click="false"
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
            :locale="userLocale"
            @change="onDateChange"
        />
    </v-menu>
    `,
});
