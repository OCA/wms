/**
 * Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

const reception_scenario = process_registry.get("reception");
// Get the original template of the reception scenario
const template = reception_scenario.component.template;
// And inject the new state template (for this module) into it
const pos = template.indexOf("</Screen>");
const new_template =
    template.substring(0, pos) +
    `
 <div v-if="state_is('set_packaging_dimension')">

    <item-detail-card
        :key="make_state_component_key(['packaging', state.data.packaging.id])"
        :record="state.data.packaging"
        :options="packaging_detail_options()"
    />

     <v-form ref="form_dimension">
        <v-container>
            <v-row>
                <v-text-field
                    label="Barcode"
                    placeholder="Packaging Barcode"
                    v-model="state.data.packaging.barcode_input"
                ></v-text-field>
            </v-row>
            <v-row>
                <v-text-field
                    label="Quantiy"
                    type="number"
                    placeholder="Packaging Quantity"
                    v-model="state.data.packaging.qty_input"
                ></v-text-field>
            </v-row>
            <v-row>
                <v-text-field
                    label="Length"
                    type="number"
                    :suffix="state.data.packaging.length_uom_name"
                    placeholder="Packaging Length"
                    v-model="state.data.packaging.packaging_length_input"
                ></v-text-field>
            </v-row>
            <v-row>
                <v-text-field
                    label="Width"
                    type="number"
                    :suffix="state.data.packaging.length_uom_name"
                    placeholder="Packaging Width"
                    v-model="state.data.packaging.width_input"
                ></v-text-field>
            </v-row>
            <v-row>
                <v-text-field
                    label="Height"
                    type="number"
                    :suffix="state.data.packaging.length_uom_name"
                    placeholder="Packaging Height"
                    v-model="state.data.packaging.height_input"
                ></v-text-field>
            </v-row>
            <v-row>
                <v-text-field
                    label="Weight"
                    type="number"
                    :suffix="state.data.packaging.weight_uom_name"
                    placeholder="Packaging Weight"
                    v-model="state.data.packaging.weight_input"
                ></v-text-field>
            </v-row>
       </v-container>
    </v-form>

    <div class="button-list button-vertical-list full">
        <v-row align="center">
            <v-col class="text-center" cols="12">
                <btn-action action="todo" @click="state.on_done">Done</btn-action>
            </v-col>
        </v-row>
        <v-row align="center">
            <v-col class="text-center" cols="12">

                <btn-action color="default" @click="state.on_skip">Skip</btn-action>

            </v-col>
        </v-row>
    </div>
</div>

` +
    template.substring(pos);

// Extend the reception scenario with :
//   - the new patched template
//   - the js code for the new state
const _get_states_base = reception_scenario.component.methods._get_states;
const baseWatchers = reception_scenario.component.watch || {};
const baseMethods = reception_scenario.component.methods || {};
const ReceptionPackageDimension = process_registry.extend("reception", {
    template: new_template,
    watch: {
        ...baseWatchers,
        "state.key": function (newState) {
            if (newState === "set_packaging_dimension") {
                this.prefill_packaging_form_inputs();
            }
        },
    },
    methods: {
        ...baseMethods,
        prefill_packaging_form_inputs: function () {
            if (!this.state_is("set_packaging_dimension")) return;

            const pkg = this.state.data.packaging;
            const input_fields = this.get_packaging_measurements_inputs();

            input_fields.forEach((inputKey) => {
                const originalKey = inputKey.replace("_input", "");
                if (pkg[inputKey] === undefined || pkg[inputKey] === null) {
                    this.$set(pkg, inputKey, pkg[originalKey]);
                }
            });
        },
        get_packaging_measurements_inputs: function () {
            return [
                "packaging_length_input",
                "width_input",
                "height_input",
                "weight_input",
                "qty_input",
                "barcode_input",
            ];
        },
        packaging_detail_options: function () {
            const pkg = this.state.data.packaging;
            const _is_field_changed = (fieldName) => {
                const inputKey = fieldName + "_input";
                return pkg[inputKey] && pkg[inputKey] != pkg[fieldName];
            };
            const options = {
                main: true,
                key_title: "name",
                title_icon: "mdi-package-variant",
                fields: [
                    {
                        path: "barcode",
                        label: "Barcode",
                        klass: _is_field_changed("barcode") ? "accent" : "",
                    },
                    {
                        path: "qty",
                        label: "Quantity",
                        klass: _is_field_changed("qty") ? "accent" : "",
                    },
                    {
                        path: "packaging_length",
                        label: "Length",
                        klass: _is_field_changed("packaging_length") ? "accent" : "",
                        renderer: function (rec, field) {
                            const value = _.result(rec, "packaging_length", "");
                            const uom = _.result(rec, "length_uom_name", "");
                            return value + " " + uom;
                        },
                    },
                    {
                        path: "width",
                        label: "Width",
                        klass: _is_field_changed("width") ? "accent" : "",
                        renderer: function (rec, field) {
                            const value = _.result(rec, "width", "");
                            const uom = _.result(rec, "length_uom_name", "");
                            return value + " " + uom;
                        },
                    },
                    {
                        path: "height",
                        label: "Height",
                        klass: _is_field_changed("height") ? "accent" : "",
                        renderer: function (rec, field) {
                            const value = _.result(rec, "height", "");
                            const uom = _.result(rec, "length_uom_name", "");
                            return value + " " + uom;
                        },
                    },
                    {
                        path: "weight",
                        label: "Weight",
                        klass: _is_field_changed("weight") ? "accent" : "",
                        renderer: function (rec, field) {
                            const value = _.result(rec, "weight", "");
                            const uom = _.result(rec, "weight_uom_name", "");
                            return value + " " + uom;
                        },
                    },
                ],
            };
            return options;
        },
        _get_states: function () {
            let states = _get_states_base.bind(this)();

            // Capture 'this' in a variable to be safe across async boundaries
            const self = this;

            states["set_packaging_dimension"] = {
                display_info: {
                    title: "Set packaging dimension",
                },
                events: {
                    go_back: "on_back",
                },
                get_payload_set_packaging_dimension: () => {
                    let values = {
                        picking_id: this.state.data.picking.id,
                        selected_line_id: this.state.data.selected_move_line.id,
                        packaging_id: this.state.data.packaging.id,
                    };
                    for (const measurement of this.get_packaging_measurements_inputs()) {
                        values[measurement.replace("_input", "")] =
                            this.state.data.packaging[measurement];
                    }
                    return values;
                },
                on_skip: async function () {
                    const payload = self.state.get_payload_set_packaging_dimension();
                    payload["skip"] = true;
                    await self.wait_call(
                        self.odoo.call("set_packaging_dimension", payload)
                    );
                    self.prefill_packaging_form_inputs();
                },
                on_done: async function () {
                    const payload = self.state.get_payload_set_packaging_dimension();
                    await self.wait_call(
                        self.odoo.call("set_packaging_dimension", payload)
                    );
                    self.prefill_packaging_form_inputs();
                },
            };
            return states;
        },
    },
});

process_registry.replace("reception", ReceptionPackageDimension);
