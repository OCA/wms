import {demotools} from "./demo.core.js";

/*
TODO: fix data as per `shopfloor.data.action`
In demo.core.js I've adjusted generated data to match checkout's format
that comes from data.move_line().
*/

var DEMO_CLUSTER_PICKING_1 = {
    find_batch: {
        next_state: "confirm_start",
        data: {
            confirm_start: demotools.makeBatch({
                pickings: [demotools.makePicking(), demotools.makePicking()],
            }),
        },
        popup: {
            body:
                "Last operation of transfer XYZ. Next operation ABC is ready to proceed.",
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
            scan_destination: {},
        },
    },
    scan_destination_pack: {
        ok: {
            next_state: "start_line",
            message: {
                message_type: "success",
                body: "Product 5 put in bin #2",
            },
            data: {
                start_line: demotools.makeBatchPickingLine(),
            },
        },
        ko: {
            next_state: "zero_check",
            message: {
                message_type: "info",
                body: "Stock check required",
            },
            data: {
                zero_check: {},
            },
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
    check_pack_lot: {},
    prepare_unload: {
        next_state: "unload_all",
        data: {
            unload_all: {},
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
};

demotools.add_case("cluster_picking", DEMO_CLUSTER_PICKING_1);
