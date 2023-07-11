/**
 * Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

const reception_scenario = process_registry.get("reception");
const _get_states = reception_scenario.component.methods._get_states;
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
        :options="{main: true, key_title: 'name', title_icon: 'mdi-package-variant'}"
    />

     <v-form ref="form_dimension">
        <v-container>
            <v-row>
                <v-text-field
                    label="Barcode"
                    placeholder="Packaging Barcode"
                    v-model="state.data.packaging.barcode"
                ></v-text-field>
            </v-row>
            <v-row>
                <v-text-field
                    label="Quantiy"
                    type="number"
                    placeholder="Packaging Quantity"
                    v-model="state.data.packaging.qty"
                ></v-text-field>
            </v-row>
            <v-row>
                <v-text-field
                    label="Length"
                    type="number"
                    :suffix="state.data.packaging.length_uom"
                    placeholder="Packaging Length"
                    v-model="state.data.packaging.length"
                ></v-text-field>
            </v-row>
            <v-row>
                <v-text-field
                    label="Width"
                    type="number"
                    :suffix="state.data.packaging.length_uom"
                    placeholder="Packaging Width"
                    v-model="state.data.packaging.width"
                ></v-text-field>
            </v-row>
            <v-row>
                <v-text-field
                    label="Height"
                    type="number"
                    :suffix="state.data.packaging.length_uom"
                    placeholder="Packaging Height"
                    v-model="state.data.packaging.height"
                ></v-text-field>
            </v-row>
            <v-row>
                <v-text-field
                    label="Max Weight"
                    type="number"
                    :suffix="state.data.packaging.weight_uom"
                    placeholder="Packaging Max Weight"
                    v-model="state.data.packaging.max_weight"
                ></v-text-field>
            </v-row>
            <!-- extend -->
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
const ReceptionPackageDimension = process_registry.extend("reception", {
    template: new_template,
    "methods.get_packaging_measurements": function () {
        return ["length", "width", "height", "max_weight", "qty", "barcode"];
    },
    "methods._get_states": function () {
        let states = _get_states.bind(this)();
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
                for (const measurement of this.get_packaging_measurements()) {
                    values[measurement] = this.state.data.packaging[measurement];
                }
                return values;
            },
            on_skip: () => {
                const payload = this.state.get_payload_set_packaging_dimension();
                payload["cancel"] = true;
                this.wait_call(this.odoo.call("set_packaging_dimension", payload));
            },
            on_done: () => {
                const payload = this.state.get_payload_set_packaging_dimension();
                this.wait_call(this.odoo.call("set_packaging_dimension", payload));
            },
        };
        return states;
    },
});

process_registry.replace("reception", ReceptionPackageDimension);
