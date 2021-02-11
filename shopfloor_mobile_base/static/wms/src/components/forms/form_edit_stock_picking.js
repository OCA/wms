/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

/* eslint-disable strict */
Vue.component("form-edit-stock-picking", {
    props: ["record", "form"],
    data: function() {
        return {
            form_values: {},
            changed: false,
        };
    },
    methods: {
        on_select: function(selected, fname) {
            this.$set(this.form_values, fname, selected.id);
            this.changed = true;
            this.$emit("change", {changed: this.changed, values: this.form_values});
        },
    },
    template: `
<div :class="['form', $options._componentTag]">

    <v-form ref="form">
        <div class="fields-wrapper">
            <separator-title>Change carrier</separator-title>
            <manual-select
                :records="form.carrier_id.select_options"
                :options="{showActions: false, initValue: record.carrier.id}"
                v-on:select="($event) => { on_select($event, 'carrier_id') }"
                />
        </div>
    </v-form>

</div>
`,
});
