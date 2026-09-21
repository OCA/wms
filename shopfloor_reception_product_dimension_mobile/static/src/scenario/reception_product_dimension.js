/**
 * Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
 * Copyright 2025 ACSONE SA/NV (https://acsone.eu)
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
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
 <div v-if="state_is('set_product_dimension')">

    <item-detail-card
        :key="make_state_component_key(['product', state.data.product.id])"
        :record="state.data.product"
        :options="{main: true, key_title: 'name', title_icon: 'mdi-card-bulleted-settings-outline'}"
    />

     <v-form ref="form_dimension">
        <v-container>
            <v-row>
                <v-text-field
                    label="Length"
                    type="number"
                    :suffix="state.data.product.dimension_uom.name"
                    placeholder="Product Length"
                    v-model="state.data.product.length"
                ></v-text-field>
            </v-row>
            <v-row>
                <v-text-field
                    label="Width"
                    type="number"
                    :suffix="state.data.product.dimension_uom.name"
                    placeholder="Product Width"
                    v-model="state.data.product.width"
                ></v-text-field>
            </v-row>
            <v-row>
                <v-text-field
                    label="Height"
                    type="number"
                    :suffix="state.data.product.dimension_uom.name"
                    placeholder="Product Height"
                    v-model="state.data.product.height"
                ></v-text-field>
            </v-row>
            <v-row>
                <v-text-field
                    label="Weight"
                    type="number"
                    placeholder="Product Weight"
                    :suffix="state.data.product.weight_uom.name"
                    v-model="state.data.product.weight"
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
const ReceptionProductDimension = process_registry.extend("reception", {
    template: new_template,
    "methods.get_product_measurements": function () {
        return ["length", "width", "height", "weight"];
    },
    "methods._get_states": function () {
        let states = _get_states.bind(this)();
        states["set_product_dimension"] = {
            display_info: {
                title: "Set product dimensions",
            },
            events: {
                go_back: "on_back",
            },
            get_payload_set_product_dimension: () => {
                let values = {
                    picking_id: this.state.data.picking.id,
                    selected_line_id: this.state.data.selected_move_line.id,
                    product: this.state.data.product.id,
                };
                for (const measurement of this.get_product_measurements()) {
                    values[measurement] = this.state.data.product[measurement];
                }
                return values;
            },
            on_skip: () => {
                const payload = this.state.get_payload_set_product_dimension();
                payload["cancel"] = true;
                this.wait_call(this.odoo.call("set_product_dimension", payload));
            },
            on_done: () => {
                const payload = this.state.get_payload_set_product_dimension();
                this.wait_call(this.odoo.call("set_product_dimension", payload));
            },
        };
        return states;
    },
});

process_registry.replace("reception", ReceptionProductDimension);
