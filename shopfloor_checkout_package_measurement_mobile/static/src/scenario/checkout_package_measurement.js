/**
 * Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

import {checkout_states} from "/shopfloor_mobile/static/wms/src/scenario/checkout_states.js";

// Get the original template of the checkout scenario
const checkout_scenario = process_registry.get("checkout");
const template = checkout_scenario.component.template;
// And inject the new state template (for this module) into it
const pos = template.indexOf("</Screen>");
const new_template =
    template.substring(0, pos) +
    `

<div v-if="state_is('package_measurement')">

    <detail-picking
        :record="state.data.picking"
        :card_color="utils.colors.color_for('screen_step_done')"
    />
    <detail-package
        :record="state.data.package"
    />

    <v-form ref="form_measurement">
        <v-container>
            <v-row>
                <v-text-field
                    label="Length"
                    type="number"
                    :suffix="state.data.package.dimension_uom.name"
                    placeholder="Package Length"
                    v-if="state.data.package_requirement.length"
                    v-model="state.data.package.length"
                    :rules="validate_measurement()"
                ></v-text-field>
            </v-row>
            <v-row>
                <v-text-field
                    label="Width"
                    type="number"
                    :suffix="state.data.package.dimension_uom.name"
                    placeholder="Package Width"
                    v-if="state.data.package_requirement.width"
                    v-model="state.data.package.width"
                    :rules="validate_measurement()"
                ></v-text-field>
            </v-row>
            <v-row>
                <v-text-field
                    label="Height"
                    type="number"
                    :suffix="state.data.package.dimension_uom.name"
                    placeholder="Package Height"
                    v-if="state.data.package_requirement.height"
                    v-model="state.data.package.height"
                ></v-text-field>
            </v-row>
            <v-row>
                <v-text-field
                    label="Shipping Weight"
                    type="number"
                    :suffix="state.data.package.weight_uom.name"
                    placeholder="Package Shipping Weight"
                    v-if="state.data.package_requirement.shipping_weight"
                    v-model="state.data.package.shipping_weight"
                    :rules="validate_measurement()"
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
                <btn-back />
            </v-col>
        </v-row>
    </div>
</div>

` +
    template.substring(pos);

// Extend the checkout scenario with :
//   - the new patched template
//   - the js code for the new state
const CheckoutWithPackageMeasurement = process_registry.extend("checkout", {
    template: new_template,
    "methods._get_states": function () {
        let states = checkout_states(this);
        states["package_measurement"] = {
            display_info: {
                title: "Set required packaging measurement",
            },
            events: {
                go_back: "on_back",
            },
            on_done: () => {
                let values = {
                    picking_id: this.state.data.picking.id,
                    package_id: this.state.data.package.id,
                };
                if (!this.$refs.form_measurement.validate()) {
                    return;
                }
                // Only update required measurement
                const measurement = ["height", "length", "shipping_weight", "width"];
                for (const measure of measurement) {
                    if (this.state.data.package_requirement[measure]) {
                        values[measure] = this.state.data.package[measure];
                    }
                }
                this.wait_call(this.odoo.call("set_package_measurement", values));
            },
        };
        return states;
    },
    "methods.validate_measurement": function () {
        return [(value) => value > 0 || "A valid positive number is required"];
    },
});

process_registry.replace("checkout", CheckoutWithPackageMeasurement);
