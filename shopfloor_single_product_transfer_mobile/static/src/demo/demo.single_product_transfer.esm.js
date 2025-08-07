/**
 * Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
 */

import {demotools} from "/shopfloor_mobile_base/static/wms/src/demo/demo.core.js";

const DEMO_CASE = {
    by_menu_id: {},
};

const location_src = demotools.makeLocation();
const picking = demotools.makePicking(
    {},
    {lines_count: 2, line_random_pack: true, line_random_dest: true}
);
const selected_move_line = picking.move_lines[0];

const single_product_transfer_menu_case = demotools.addAppMenu(
    {
        name: "Single product transfer",
        scenario: "single_product_transfer",
        picking_types: [{id: 27, name: "Random type"}],
    },
    "sprt_1"
);

const DEMO_SINGLE_PRODUCT_TRANSFER = {
    start: {
        next_state: "scan_location",
        data: {},
    },
    scan_location: {
        next_state: "select_product",
        data: {
            select_product: {
                location: location_src,
            },
        },
    },
    scan_product: {
        next_state: "set_quantity",
        data: {
            set_quantity: {
                picking,
                selected_move_line,
            },
        },
    },
    set_quantity: function (scanned) {
        // Different behaviour depending on the first letter of the scanned barcode:
        // - P: Scanned product, increase qty_done and stay in the same screen.
        // - L: Scanned location, go to screen 1.
        // - Else: Display warning message.
        const barcode = scanned.barcode;
        if (barcode[0] === "P") {
            selected_move_line.qty_done++;
            return {
                next_state: "set_quantity",
                data: {
                    set_quantity: {
                        picking,
                        selected_move_line,
                    },
                },
            };
        } else if (barcode[0] === "L") {
            return {
                next_state: "show_completion_info",
                data: {},
            };
        }
        return {
            next_state: "set_quantity",
            data: {
                set_quantity: {
                    picking,
                    selected_move_line,
                },
            },
            message: {
                message_type: "warning",
                body: "Barcode is wrong",
            },
        };
    },
};

DEMO_CASE.by_menu_id[single_product_transfer_menu_case] = DEMO_SINGLE_PRODUCT_TRANSFER;

demotools.add_case("single_product_transfer", DEMO_CASE);
