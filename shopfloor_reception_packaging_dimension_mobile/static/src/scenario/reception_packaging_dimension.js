/**
 * Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";
import "/shopfloor_reception_packaging_dimension_mobile/static/src/components/form_edit_product_packaging.js";

const reception_scenario = process_registry.get("reception");
// Get the original template of the reception scenario
const template = reception_scenario.component.template;
// And inject the new state template (for this module) into it
const pos = template.indexOf("</Screen>");
const new_template =
    template.substring(0, pos) +
    `
<div v-if="state_is('set_packaging_dimension')">
    <form-edit-product-packaging :packaging="state.data.packaging" :allowEditName="false" @done="this.state.on_done" @skip="this.state.on_skip"/>
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
    methods: {
        ...baseMethods,
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
                _handle_dimension_submission: async function (
                    is_skip = false,
                    new_packaging_data = {}
                ) {
                    let payload = {
                        picking_id: self.state.data.picking.id,
                        selected_line_id: self.state.data.selected_move_line.id,
                        packaging_id: self.state.data.packaging.id,
                        ...new_packaging_data,
                    };
                    if (is_skip) {
                        payload["skip"] = true;
                    }

                    await self.wait_call(
                        self.odoo.call("set_packaging_dimension", payload)
                    );

                    self.$nextTick(() => {
                        window.scrollTo(0, 0);
                    });
                },
                on_skip: async function () {
                    await self.state._handle_dimension_submission(true);
                },
                on_done: async function (event) {
                    await self.state._handle_dimension_submission(false, event);
                },
            };
            return states;
        },
    },
});

process_registry.replace("reception", ReceptionPackageDimension);
