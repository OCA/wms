/* eslint no-use-before-define: 0 */ // --> OFF

var DEMO_CHECKOUT = {
    "scan_document": {
        "PACK1" : {
            // No picking
            "next_state": "select_document",
            "message": {
                "message_type": "error",
                "message": "No picking found for PACK1",
            },
        },
        "PACK2" : {
            // All line have a destination pack
            "next_state": "select_line",
            "data": {
                "select_line": makePicking(5),
            },
        },
    },
    "list_batch": {
        "next_state": "manual_selection",
        "message": {
            "message_type": "success",
            "message": "Previous line postponed",
        },
        "data": {
            // Next line to process
            "manual_selection": {
                "records": batchList(15),
            },
        },
    },
    // TODO
    "select_line": {
        "next_state": "select_pack",
        "data": {
            "select_pack": makePicking({"with_lines": 5, "random_pack": true}),
        },
    },
    "confirm_start": {
        "next_state": "start_line",
        "data": {
            "start_line": makeBatchPickingLine(),
        },
    },
    "unassign": {
        "next_state": "start",
    },
    "scan_line": {
        "next_state": "scan_destination",
        "data": {
            "scan_destination": {

            },
        },
    },
    "scan_destination_pack": {
        "ok": {
            "next_state": "start_line",
            "message": {
                "message_type": "success",
                "message": "Product 5 put in bin #2",
            },
            "data": {
                "start_line": makeBatchPickingLine(),
            },
        },
        "ko": {
            "next_state": "zero_check",
            "message": {
                "message_type": "info",
                "message": "Stock check required",
            },
            "data": {
                "zero_check": {},
            },
        },
    },
    "stock_is_zero": {
        "next_state": "start_line",
        "message": {
            "message_type": "success",
            "message": "Stock zero confirmed",
        },
        "data": {
            // Next line to process
            "start_line": makeBatchPickingLine(),
        },
    },
    "skip_line": {
        "next_state": "start_line",
        "message": {
            "message_type": "success",
            "message": "Previous line postponed",
        },
        "data": {
            // Next line to process
            "start_line": makeBatchPickingLine(),
        },
    },
    "stock_issue": {
        "next_state": "start_line",
        "message": {
            "message_type": "success",
            "message": "Stock out confirmed",
        },
        "data": {
            // Next line to process
            "start_line": makeBatchPickingLine(),
        },
    },
    "check_pack_lot": {},
    "prepare_unload": {
        "next_state": "unload_all",
        "data": {
            "unload_all": {

            },
        },
    },
    "set_destination_all": {
        "OK": {
            "next_state": "start_line",
            "message": {
                "message_type": "success",
                "message": "Destination set",
            },
            "data": {
                // Next line to process
                "start_line": makeBatchPickingLine(),
            },
        },
        "KO": {
            "next_state": "confirm_unload_all",
            "data": {
                // Next line to process
                "unload_all": {},
            },
            "message": {
                "message_type": "warning",
                "message": "Confirm you want to unload them all?",
            },
        },
    },
    "unload_split": {},
    "unload_scan_pack": {},
    "unload_scan_destination": {},
    "unload_router": {},
};

window.DEMO_CASES.checkout = DEMO_CHECKOUT;

/* eslint no-use-before-define: 2 */ // --> ON
