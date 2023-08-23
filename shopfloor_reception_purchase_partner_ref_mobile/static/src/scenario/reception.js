/**
 * Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
 */

import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

const reception_scenario = process_registry.get("reception");
const select_dest_package_display_name_values =
    reception_scenario.component.methods.select_dest_package_display_name_values;
const picking_display_fields =
    reception_scenario.component.methods.picking_display_fields;

const ReceptionPartnerRef = process_registry.extend("reception", {
    "methods.select_dest_package_display_name_values": function (rec) {
        var values = select_dest_package_display_name_values.bind(this)(rec);
        if (rec.purchase_order.partner_ref) {
            values.splice(1, 0, rec.purchase_order.partner_ref);
        }
        return values;
    },
    "methods.picking_display_fields": function () {
        var fields = picking_display_fields.bind(this)();
        fields.splice(1, 0, {
            path: "purchase_order.partner_ref",
            label: "Vendor Reference",
        });
        return fields;
    },
});

process_registry.replace("reception", ReceptionPartnerRef);
