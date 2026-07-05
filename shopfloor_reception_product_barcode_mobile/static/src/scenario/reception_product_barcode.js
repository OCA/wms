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
 <div v-if="state_is('set_product_barcode')">

    <searchbar
        v-on:found="on_scan"
        :input_placeholder="search_input_placeholder"
    />

    <item-detail-card
        :key="make_state_component_key(['product', state.data.product.id])"
        :record="state.data.product"
        :options="{main: true, key_title: 'name', title_icon: 'mdi-barcode'}"
    />

     <v-form ref="form_dimension">
        <v-container>
            <v-row>
                <v-text-field
                    label="Barcode"
                    placeholder="Product Barcode"
                    v-model="state.data.product_barcode"
                    v-on="on_scan"
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
const ReceptionProductBarcode = process_registry.extend("reception", {
    template: new_template,
    "methods._get_states": function () {
        let states = _get_states.bind(this)();
        states["set_product_barcode"] = {
            display_info: {
                title: "Set product barcode",
                scan_placeholder: "Scan product barcode",
            },
            events: {
                go_back: "on_back",
            },
            on_scan: (barcode) => {
                this.wait_call(
                    this.odoo
                        .call("set_product_barcode_scan", {
                            barcode: barcode.text,
                            picking_id: this.state.data.picking.id,
                            selected_line_id: this.state.data.selected_move_line.id,
                        })
                        .then((res) => {
                            this.state_set_data({
                                product_barcode:
                                    res.data.set_product_barcode.product_barcode,
                            });
                            return res;
                        })
                );
            },
            get_payload_set_product_barcode: () => {
                let values = {
                    picking_id: this.state.data.picking.id,
                    selected_line_id: this.state.data.selected_move_line.id,
                    product: this.state.data.product.id,
                };
                values["barcode"] = this.state.data.product_barcode;
                return values;
            },
            on_skip: () => {
                const payload = this.state.get_payload_set_product_barcode();
                payload["cancel"] = true;
                this.wait_call(this.odoo.call("set_product_barcode", payload));
            },
            on_done: () => {
                const payload = this.state.get_payload_set_product_barcode();
                this.wait_call(this.odoo.call("set_product_barcode", payload));
            },
        };
        return states;
    },
});

process_registry.replace("reception", ReceptionProductBarcode);
