/* eslint no-use-before-define: 0 */  // --> OFF

var CASE_1 = {
    'fetch' : {
        "data": {
            "id": 1,
            "name": "A nice pack 1",
            "location_src": {
                "id": 1,
                "name":  'Location SRC 1',
            },
            "location_dst": {
                "id": 2,
                "name": 'Location SRC 2',
            },
            "product": {"id": 1, "name": 'Product 1'},
            "picking": {"id": 1, "name": 'Picking 1'},
        },
        "state": "scan_location",
        "message": undefined
    },
    'validate' : {
        "data": undefined,
        "state": "scan_pack",
        "message": {
            'body': 'Pack validated',
            'message_type': 'info',
        }
    },
    'cancel' : {
        "data": {
            "id": 1,
            "location_src": {
                "id": 1,
                "name":  'Location SRC 1 cancel',
            },
            "location_dst": {
                "id": 2,
                "name": 'Location DST 1 cancel',
            },
            "product": {"id": 1, "name": 'Product 1'},
            "picking": {"id": 1, "name": 'Picking 1'},
        },
        "state": "scan_location",
        "message": undefined
    }
}

var CASE_2 = {
    'fetch' : {
        "data": undefined,
        "state": "scan_pack",
        "message": {"message_type": "error", "body": "You cannot do that!"}
    },
}
var CASE_3 = {
    'fetch' : {
        "data": undefined,
        "state": "scan_pack",
        "message": {"message_type": "error", "body": "No pkg found"}
    },
}
var CASE_4 = {
    'fetch' : {
        "data": {
            "id": 1,
            "name": "A nice pack 4",
            "location_src": {
                "id": 1,
                "name":  'Location SRC 4',
            },
            "location_dst": {
                "id": 2,
                "name": 'Location DST 4',
            },
            "product": {"id": 1, "name": 'Product 4'},
            "picking": {"id": 1, "name": 'Picking 4'},
        },
        "state": "takeover",
        "message": {"message_type": "info", "body": "Benoit is at the toilette: do you take over?"}
    },
    'validate' : {
        "data": undefined,
        "state": "scan_pack",
        "message": {
            'body': 'Pack validated',
            'message_type': 'info',
        }
    },
}
var CASE_5 = {
    'fetch' : {
        "data": {
            "id": 1,
            "name": "A nice pack 5",
            "location_src": {
                "id": 1,
                "name":  'Location SRC 5',
            },
            "location_dst": {
                "id": 2,
                "name": 'Location DST 5',
            },
            "product": {"id": 1, "name": 'Product 5'},
            "picking": {"id": 1, "name": 'Picking 5'},
        },
        "state": "scan_location",
        "message": undefined
    },
    'cancel' : {
        "data": undefined,
        "state": "scan_pack",
        "message": undefined,
    },
    'validate' : {
        "data": undefined,
        "state": "scan_pack",
        "message": {
            'body': 'Pack validated',
            'message_type': 'info',
        }
    },
}
var CASE_6 = {
    'fetch' : {
        "data": {
            "id": 1,
            "name": "A nice pack 6",
            "location_src": {
                "id": 1,
                "name":  'Location SRC 6',
            },
            "location_dst": {
                "id": 2,
                "name": 'Location DST 6',
            },
            "product": {"id": 1, "name": 'Product 6'},
            "picking": {"id": 1, "name": 'Picking 6'},
        },
        "state": "scan_location",
        "message": undefined
    },
    'validate' : {
        "data": undefined,
        "state": "confirm_location",
        "message": {"message_type": "warning", "body": "Are you sure of this location?"}
    },
    'LOC6' : {
        "data": undefined,
        "state": "scan_pack",
        "message": {
            'body': 'Pack validated',
            'message_type': 'info',
        }
    },
}
var CASE_7 = {
    'fetch' : {
        "data": {
            "id": 1,
            "name": "A nice pack 7",
            "location_src": {
                "id": 1,
                "name":  'Location SRC 7',
            },
            "location_dst": {
                "id": 2,
                "name": 'Location DST 7',
            },
            "product": {"id": 1, "name": 'Product 7'},
            "picking": {"id": 1, "name": 'Picking 7'},
        },
        "state": "scan_location",
        "message": undefined
    },
    'validate' : {
        "data": undefined,
        "state": "scan_location",
        "message": {"message_type": "error", "body": "You cannot move to this location"}
    },
    'LOC7' : {
        "data": undefined,
        "state": "scan_pack",
        "message": {
            'body': 'Pack validated',
            'message_type': 'info',
        }
    },
}



window.CASES = {
    "1": CASE_1,
    "2": CASE_2,
    "3": CASE_3,
    "4": CASE_4,
    "5": CASE_5,
    "6": CASE_6,
    "7": CASE_7,
};

window.CASE = window.CASES["1"];

/* eslint no-use-before-define: 2 */  // --> ON