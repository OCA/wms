/**
 * Copyright 2025 ACSONE SA/NV (https://acsone.eu)
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
 */

import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

const location_content_transfer_scenario = process_registry.get(
    "location_content_transfer"
);

// Inject the new state template into already exiting one
const template = location_content_transfer_scenario.component.template;
const pos = template.indexOf("</Screen>");
const new_template =
    template.substring(0, pos) +
    `
 <template v-if="state_is('scan_destination_all') && this._print_label_allowed()">
    <label-printer v-on:print_labels="print_labels($event)" buttonLabel="Print Labels"/>
 </template>

` +
    template.substring(pos);

// Create a new component extending the location_content_transfer scenario
const LocationContentTransfer = process_registry.extend("location_content_transfer", {
    template: new_template,

    methods: {
        ...location_content_transfer_scenario.component.methods,

        print_labels: function (quantity) {
            this.wait_call(
                this.odoo.call("print_labels", {
                    move_line_ids: this.state.data.move_lines.map((x) => x.id),
                    quantity: quantity,
                })
            );
        },
    },
});

process_registry.replace("location_content_transfer", LocationContentTransfer);

export default LocationContentTransfer;
