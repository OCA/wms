/**
 * Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {demotools} from "/shopfloor_mobile_base/static/wms/src/demo/demo.core.js";

const DEMO_CASE = {
    by_menu_id: {},
};

const manual_product_transfer_menu_id = demotools.addAppMenu({
    name: "Manual Product Transfer",
    scenario: "manual_product_transfer",
    picking_types: [{id: 27, name: "Random type"}],
});
const single_line_case_move_line = demotools.makeSingleLineOperation();
const source_location = demotools.makeLocation();
const MANUAL_PRODUCT_TRANSFER_CASE = {
    start: {
        next_state: "scan_source_location",
        message: {
            message_type: "info",
            body: "Pprevious line processed info.",
        },
        data: {
            scan_source_location: {
                move_line: _.cloneDeep(single_line_case_move_line),
            },
        },
    },
    scan_source_location: {
        next_state: "scan_product",
        message: {
            message_type: "info",
            body: "Recovered line from previous session.",
        },
        data: {
            scan_source_location: {
                location: _.cloneDeep(source_location),
            },
        },
    },
    scan_product: {
        next_state: "scan_destination_location",
        message: {
            message_type: "info",
            body: "Recovered line from previous session.",
        },
        data: {
            scan_product: {
                location: _.cloneDeep(single_line_case_move_line),
            },
        },
    },
    scan_destination_location: {
        next_state: "scan_source_location",
        message: {
            message_type: "info",
            body: "Destination set on the line",
        },
        data: {
            scan_destination_location: {
                move_line: _.cloneDeep(single_line_case_move_line),
            },
        },
    },
};
DEMO_CASE.by_menu_id[manual_product_transfer_menu_id] = MANUAL_PRODUCT_TRANSFER_CASE;

demotools.add_case("manual_product_transfer", DEMO_CASE);
