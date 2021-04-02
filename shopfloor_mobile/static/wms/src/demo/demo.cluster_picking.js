/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {demotools} from "/shopfloor_mobile_base/static/wms/src/demo/demo.core.js";

const DEMO_CLUSTER_PICKING_1 = {
    find_batch: {
        next_state: "confirm_start",
        data: {
            confirm_start: demotools.makeBatch({
                pickings: [demotools.makePicking(), demotools.makePicking()],
            }),
        },
    },
    list_batch: {
        next_state: "manual_selection",
        message: {
            message_type: "success",
            body: "Previous line postponed",
        },
        data: {
            // Next line to process
            manual_selection: {
                records: demotools.batchList(15),
            },
        },
    },
    select: {
        next_state: "confirm_start",
        data: {
            confirm_start: demotools.makeBatch({
                pickings: [demotools.makePicking(), demotools.makePicking()],
            }),
        },
    },
    confirm_start: {
        next_state: "start_line",
        data: {
            start_line: demotools.makeBatchPickingLine(),
        },
    },
    unassign: {
        next_state: "start",
    },
    scan_line: {
        next_state: "scan_destination",
        data: {
            scan_destination: demotools.makeBatchPickingLine(),
        },
    },
    scan_destination_pack: {
        next_state: "start_line",
        message: {
            message_type: "success",
            body: "Product 5 put in bin #2",
        },
        data: {
            start_line: demotools.makeBatchPickingLine(),
        },
    },
    stock_is_zero: {
        next_state: "start_line",
        message: {
            message_type: "success",
            body: "Stock zero confirmed",
        },
        data: {
            // Next line to process
            start_line: demotools.makeBatchPickingLine(),
        },
    },
    skip_line: {
        next_state: "start_line",
        message: {
            message_type: "success",
            body: "Previous line postponed",
        },
        data: {
            // Next line to process
            start_line: demotools.makeBatchPickingLine(),
        },
    },
    stock_issue: {
        /*
        # when we still have lines to process
        "start_line",
        # when all lines have been processed and have same
        # destination
        "unload_all",
        # when all lines have been processed and have different
        # destinations
        "unload_single",
        */
        next_state: "start_line",
        message: {
            message_type: "success",
            body: "Stock out confirmed",
        },
        data: {
            // Next line to process
            start_line: demotools.makeBatchPickingLine(),
        },
    },
    change_pack_lot: {
        // "change_pack_lot", "scan_destination"
        next_state: "scan_destination",
        data: {
            scan_destination: _.extend({}, demotools.makeBatchPickingLine(), {
                package_dest: demotools.makePack(),
            }),
        },
    },
    prepare_unload: {
        next_state: "unload_all",
        data: {
            unload_all: _.extend({}, demotools.makeBatch(), {
                location_dest: demotools.makeLocation(),
            }),
        },
    },
    set_destination_all: {
        OK: {
            next_state: "start_line",
            message: {
                message_type: "success",
                body: "Destination set",
            },
            data: {
                // Next line to process
                start_line: demotools.makeBatchPickingLine(),
            },
        },
        KO: {
            next_state: "confirm_unload_all",
            data: {
                // Next line to process
                unload_all: {},
            },
            message: {
                message_type: "warning",
                body: "Confirm you want to unload them all?",
            },
        },
    },
    unload_split: {},
    unload_scan_pack: {},
    unload_scan_destination: {},
    unload_router: {},
    // TODO
    popup: {
        body: "Last operation of transfer XYZ. Next operation ABC is ready to proceed.",
    },
};

demotools.add_case("cluster_picking", DEMO_CLUSTER_PICKING_1);
