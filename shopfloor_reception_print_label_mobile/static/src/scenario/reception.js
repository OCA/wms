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
 <template v-if="state_is('set_destination') && this._print_label_allowed()">

    <label-printer v-on:print_labels="state.print_labels($event)" buttonLabel="Print Labels"/>

 </template>

` +
    template.substring(pos);

// Extend the reception scenario with :
//   - the new patched template
//   - the js code for the new state
const ReceptionProductBarcode = process_registry.extend("reception", {
    template: new_template,
    "methods._get_states": function () {
        let states = _get_states.bind(this)();
        const set_destination = states.set_destination;

        const self = this;
        set_destination.print_labels = function (quantity) {
            self.wait_call(
                self.odoo.call("print_labels", {
                    picking_id: self.state.data.picking.id,
                    selected_line_id: self.state.data.selected_move_line[0].id,
                    quantity: quantity,
                })
            );
        };
        return states;
    },
});

process_registry.replace("reception", ReceptionProductBarcode);
