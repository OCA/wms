import {demotools} from './demo.core.js';


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
                "select_line": demotools.makePicking({"lines_count": 5, "line_random_pack": true}),
            },
        },
    },
    "list_stock_picking": {
        "next_state": "manual_selection",
        "message": null,
        "data": {
            "manual_selection": {
                "records": _.sampleSize([
                    demotools.makePicking(),
                    demotools.makePicking(),
                    demotools.makePicking(),
                    demotools.makePicking(),
                    demotools.makePicking(),
                    demotools.makePicking(),
                    demotools.makePicking(),
                    demotools.makePicking(),
                ], _.random(8)),
            },
        },
    },

    // TODO
    "select_line": {
        "next_state": "select_pack",
        "data": {
            "select_pack": demotools.makePicking({"lines_count": 5, "line_random_pack": true, "line_random_dest": true}),
        },
    },
    // TODO
    "summary": {
        "next_state": "summary",
        "data": {
            "summary": demotools.makePicking({"lines_count": 5, "line_random_pack": true}),
        },
    },
};


demotools.add_case('checkout', DEMO_CHECKOUT);
