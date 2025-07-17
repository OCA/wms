/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * Copyright 2025 ACSONE SA/NV (https://acsone.eu)
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
 */

export var LabelPrinterWidget = Vue.component("label-printer", {
    template: `
<div :class="['number-spinner', 'spinner-' + mode]">
 <v-row dense align="center">
        <v-col>

         <div class="input-wrapper">
            <v-text-field class="current-value" :type="input_type" v-model="value" :disabled="!editable" />
            <div v-if="show_init_value" class="init-value">
                <span>{{ original_value }}</span>
            </div>
        </div>

        </v-col>
        <v-col>
        <div class="spinner-btn minus" v-on:click="decrease()">
            <slot name="minus"><span>-</span></slot>
        </div>
        </v-col>
        <v-col>
        <div class="spinner-btn plus" v-on:click="increase()">
            <slot name="plus"><span>+</span></slot>
        </div>
        </v-col>
        <v-col >
           <btn-action class="x-small" action="todo" @click="$emit('print_labels', value)">{{ get_label() }}</btn-action>
        </v-col>
    </v-row>
</div>
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
