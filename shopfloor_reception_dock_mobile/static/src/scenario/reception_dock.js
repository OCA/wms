/**
 * Copyright 2026 ACSONE SA/NV
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

const reception_scenario = process_registry.get("reception");
const baseMethods = reception_scenario.component.methods || {};
const original_picking_display_fields =
    reception_scenario.component.methods.picking_display_fields;

const ReceptionDock = process_registry.extend("reception", {
    methods: {
        ...baseMethods,
        picking_display_fields: function (...args) {
            let res = [];
            if (original_picking_display_fields) {
                res = original_picking_display_fields.apply(this, args);
            }

            res.push({
                path: "docks",
                visible: (rec) => rec.docks && rec.docks.length > 0,
                renderer: (rec) => {
                    if (!rec.docks || rec.docks.length === 0) {
                        return null;
                    }
                    const dockNames = rec.docks.map((dock) => dock.name).join(", ");
                    return "Docks: " + dockNames;
                },
            });
            return res;
        },
    },
});

process_registry.replace("reception", ReceptionDock);
