/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

export var NumberSpinner = Vue.component("input-number-spinner", {
    template: `

<div :class="['number-spinner', 'spinner-' + mode]">
    <div class="spinner-btn plus" v-on:click="increase()" v-if="mode != 'text-only'">
        <slot name="plus"><span>+</span></slot>
    </div>
    <div class="input-wrapper">
        <v-text-field class="current-value" :type="input_type" v-model="value" :disabled="!editable" />
        <div v-if="show_init_value" class="init-value">
            <span>{{ original_value }}</span>
        </div>
    </div>
    <div class="spinner-btn minus" v-on:click="decrease()" v-if="mode != 'text-only'">
        <slot name="minus"><span>-</span></slot>
    </div>
</div>
`,
    props: {
        input_type: {
            type: String,
            default: "text", // Avoid default browser spinner
        },
        init_value: {
            type: Number,
            default: 0,
        },
        min: {
            type: Number,
            default: 0,
        },
        max: {
            type: Number,
            default: undefined,
        },
        step: {
            type: Number,
            default: 1,
        },
        editable: {
            type: Boolean,
            default: true,
        },
        mode: {
            type: String,
            default: "text-only",
        },
        show_init_value: {
            type: Boolean,
            default: true,
        },
        select_value_on_load: {
            type: Boolean,
            default: true,
        },
    },
    data: function() {
        return {
            value: 0,
            original_value: 0,
        };
    },
    methods: {
        increase: function() {
            if (this.max == undefined || this.value < this.max) {
                this.value += this.step;
            }
        },
        decrease: function() {
            if (this.value > this.min) {
                const new_val = this.value - this.step;
                this.value = new_val >= this.min ? new_val : this.min;
            }
        },
    },
    watch: {
        value: {
            handler: function(newVal, oldVal) {
                this.value = newVal;
                this.$emit("input", this.value);
            },
        },
    },
    created: function() {
        this.original_value = parseInt(this.init_value, 10);
        this.value = parseInt(this.init_value, 10);
    },
    mounted: function() {
        if (this.$props.select_value_on_load) {
            const input = $("input", this.$el).get(0);
            input.focus();
            input.select();
        }
    },
});
