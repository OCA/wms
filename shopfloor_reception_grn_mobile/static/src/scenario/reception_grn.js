/**
 * Copyright 2026 ACSONE SA/NV
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

const reception_scenario = process_registry.get("reception");

const ReceptionGrn = process_registry.extend("reception", {
    methods: {
        ...(reception_scenario.component.methods || {}),
        picking_display_fields: function (...args) {
            let base_picking_display_fields =
                reception_scenario.component.methods.picking_display_fields;

            let res = [];
            if (base_picking_display_fields) {
                res = base_picking_display_fields.apply(this, args);
            }

            res.push({
                path: "grn.name",
                label: "GRN",
            });
            return res;
        },
        _get_states: function () {
            let _get_states_base = reception_scenario.component.methods._get_states;
            let states = _get_states_base.bind(this)();

            // Capture 'this' in a variable to be safe across async boundaries
            const self = this;

            states["select_document"]["display_info"]["scan_placeholder"] += " / GRN";

            return states;
        },
    },
});

process_registry.replace("reception", ReceptionGrn);
