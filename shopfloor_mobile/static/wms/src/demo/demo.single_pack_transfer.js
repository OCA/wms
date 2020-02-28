/* eslint no-use-before-define: 0 */ // --> OFF
/* eslint no-use-before-define: 0 */ // --> OFF
var CANCEL_MSG_DEFAULT = {
    "message": "Operation cancelled",
    "message_type": "info",
};


var DEMO_SINGLE_PACK_TRANSFER_1 = {
    "start" : {
        "data": {
            "scan_location": {
                "type": "pack",
                "id": 1,
                "name": "A nice pack 1",
                "location_src": {
                    "id": 1,
                    "name":  "Location SRC 1",
                },
                "location_dst": {
                    "id": 2,
                    "name": "Location SRC 2",
                },
                "product": [{"id": 1, "name": "Product 1", "qty": 5}, {"id": 2, "name": "Product 2", "qty": 2}],
                "picking": {"id": 1, "name": "Picking 1"},
            },
        },
        "next_state": "scan_location",
        "message": undefined,
    },
    "validate" : {
        "data": undefined,
        "next_state": "start",
        "message": {
            "message": "Pack validated",
            "message_type": "success",
        },
    },
    "cancel" : {
        "next_state": "start",
        "message": CANCEL_MSG_DEFAULT,
    },
    "LOC1" : {
        "data": undefined,
        "next_state": "start",
        "message": {
            "message": "Pack validated",
            "message_type": "success",
        },
    },
    "LOC2" : {
        "data": {
            "show_completion_info": {
                "last_operation_name": "Last operation XYZ",
                "next_operation_name": "Next operation XYZ",
            },
        },
        "next_state": "show_completion_info",
        "message": {},
    },
    "LOC3" : {
        "data": undefined,
        "next_state": "start",
        "message": {
            "message": "Pack validated",
            "message_type": "success",
        },
    },
};

window.DEMO_CASES.single_pack_transfer = DEMO_SINGLE_PACK_TRANSFER_1;
/* eslint no-use-before-define: 2 */ // --> ON
