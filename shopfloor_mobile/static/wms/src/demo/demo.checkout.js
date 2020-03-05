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
                "select_line": makePicking({"with_lines": 5, "random_pack": true}),
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
};

window.DEMO_CASES.checkout = DEMO_CHECKOUT;

/* eslint no-use-before-define: 2 */ // --> ON
