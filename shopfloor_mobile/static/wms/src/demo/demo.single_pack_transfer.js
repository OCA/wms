/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {demotools} from "/shopfloor_mobile_base/static/wms/src/demo/demo.core.js";

// TODO: refactor w/ demotools data
const CANCEL_MSG_DEFAULT = {
    body: "Operation cancelled",
    message_type: "info",
};

const DEMO_SINGLE_PACK_TRANSFER_1 = {
    start: {
        data: {
            scan_location: {
                // FIXME: outdated data here
                type: "package",
                id: 1,
                name: "A nice pack 1",
                location_src: {
                    id: 1,
                    name: "Location SRC 1",
                    barcode: "loc1",
                },
                location_dest: {
                    id: 2,
                    name: "Location DST 2",
                    barcode: "loc2",
                },
                product: [
                    {id: 1, name: "Product 1", qty: 5},
                    {id: 2, name: "Product 2", qty: 2},
                ],
                picking: {id: 1, name: "Picking 1"},
            },
        },
        next_state: "scan_location",
        message: undefined,
    },
    validate: {
        data: undefined,
        next_state: "start",
        message: {
            body: "Pack validated",
            message_type: "success",
        },
    },
    cancel: {
        next_state: "start",
        message: CANCEL_MSG_DEFAULT,
    },
    LOC1: {
        data: undefined,
        next_state: "start",
        message: {
            body: "Pack validated",
            message_type: "success",
        },
    },
    LOC2: {
        data: {
            show_completion_info: {
                last_operation_name: "Last operation XYZ",
                next_operation_name: "Next operation XYZ",
            },
        },
        next_state: "show_completion_info",
        message: {},
    },
    LOC3: {
        data: undefined,
        next_state: "start",
        message: {
            body: "Pack validated",
            message_type: "success",
        },
    },
};

demotools.add_case("single_pack_transfer", DEMO_SINGLE_PACK_TRANSFER_1);
