/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * Copyright 2025 ACSONE SA/NV (https://acsone.eu)
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
 */

export var LabelPrinterWidget = Vue.component("label-printer", {
    template: `
<v-card class="d-flex flex-column pb-2 pl-2 pr-2">
    <v-card-title class="overline">
        Label Printing
    </v-card-title>

    <div class="d-flex mb-2 ">
        <v-btn rounded outlined color="primary" @click="decrease">
            <v-icon small>mdi-minus</v-icon>
        </v-btn>

        <v-text-field
            v-model.number="value"
            :rules="numberRules"
            dense
            class="centered-input"
        />

        <v-btn rounded outlined color="primary" @click="increase">
            <v-icon small>mdi-plus</v-icon>
        </v-btn>
    </div>

    <btn-action class="x-small" action="todo" @click="$emit('print_labels', value)">{{ get_label() }}</btn-action>
</v-card>
`,
    props: {
        input_type: {
            type: String,
            default: "text", // Avoid default browser spinner
        },
        editable: {
            type: Boolean,
            default: true,
        },
        show_init_value: {
            type: Boolean,
            default: false,
        },
        select_value_on_load: {
            type: Boolean,
            default: true,
        },
        step: {
            type: Number,
            default: 1,
        },
        buttonLabel: {
            type: String,
            default: "Print",
        },
        min: {
            type: Number,
            default: 1,
        },
        mode: {
            type: String,
            default: "text-only",
        },
    },
    data: function () {
        return {
            value: 1,
            original_value: 0,

            // Data validation for the number input field
            numberRules: [
                (v) => !!v || "Required",
                (v) => Number.isInteger(Number(v)) || "Must be a number",
            ],
        };
    },
    methods: {
        get_label: function () {
            return this.buttonLabel;
        },
        increase: function () {
            if (this.max == undefined || this.value < this.max) {
                this.value += this.step;
            }
        },
        decrease: function () {
            if (this.value > this.min) {
                const new_val = this.value - this.step;
                this.value = new_val >= this.min ? new_val : this.min;
            }
        },
    },
    watch: {
        value: {
            handler: function (newVal, oldVal) {
                this.value = newVal;
                this.$emit("input", this.value);
            },
        },
    },
});
