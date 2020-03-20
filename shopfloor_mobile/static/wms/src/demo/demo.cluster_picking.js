/* eslint no-use-before-define: 0 */ // --> OFF

var DEMO_CLUSTER_PICKING_1 = {
    find_batch: {
        next_state: "confirm_start",
        data: {
            confirm_start: {
                id: 100,
                name: "BATCH001",
                picking_count: 3,
                move_line_count: 6,
                pickings: [
                    {
                        id: 1,
                        name: "OP001",
                        customer: {
                            name: "Customer 1",
                        },
                        origin: "SO000CUST001",
                        move_line_count: 4,
                    },
                    {
                        id: 2,
                        name: "OP002",
                        customer: {
                            name: "Customer 2",
                        },
                        origin: "SO000CUST002",
                        move_line_count: 2,
                    },
                ],
            },
        },
    },
    list_batch: {
        next_state: "manual_selection",
        message: {
            message_type: "success",
            message: "Previous line postponed",
        },
        data: {
            // Next line to process
            manual_selection: {
                records: batchList(15),
            },
        },
    },
    select: {
        next_state: "confirm_start",
        data: {
            confirm_start: {
                id: 100,
                name: "BATCHXXX",
                picking_count: 3,
                move_line_count: 6,
                records: [
                    {
                        id: 1,
                        name: "OP001",
                        customer: {
                            name: "Customer 1",
                        },
                        origin: "SO000CUST001",
                        move_line_count: 4,
                    },
                    {
                        id: 2,
                        name: "OP002",
                        customer: {
                            name: "Customer 2",
                        },
                        origin: "SO000CUST002",
                        move_line_count: 2,
                    },
                ],
            },
        },
    },
    confirm_start: {
        next_state: "start_line",
        data: {
            start_line: makeBatchPickingLine(),
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
                message: "Product 5 put in bin #2",
            },
            data: {
                start_line: makeBatchPickingLine(),
            },
        },
        ko: {
            next_state: "zero_check",
            message: {
                message_type: "info",
                message: "Stock check required",
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
            message: "Stock zero confirmed",
        },
        data: {
            // Next line to process
            start_line: makeBatchPickingLine(),
        },
    },
    skip_line: {
        next_state: "start_line",
        message: {
            message_type: "success",
            message: "Previous line postponed",
        },
        data: {
            // Next line to process
            start_line: makeBatchPickingLine(),
        },
    },
    stock_issue: {
        next_state: "start_line",
        message: {
            message_type: "success",
            message: "Stock out confirmed",
        },
        data: {
            // Next line to process
            start_line: makeBatchPickingLine(),
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
                message: "Destination set",
            },
            data: {
                // Next line to process
                start_line: makeBatchPickingLine(),
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
                message: "Confirm you want to unload them all?",
            },
        },
    },
    unload_split: {},
    unload_scan_pack: {},
    unload_scan_destination: {},
    unload_router: {},
};

window.DEMO_CASES.cluster_picking = DEMO_CLUSTER_PICKING_1;

/* eslint no-use-before-define: 2 */ // --> ON
