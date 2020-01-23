var CASE_1 = {
    'fetch' : {
        "data": {
            "id": 1,
            "location_src": {
                "id": 1,
                "name":  'Location foo baz',
            },
            "location_dst": {
                "id": 2,
                "name": 'Location bar',
            },
            "product": {"id": 1, "name": 'product name'},
            "picking": {"id": 1, "name": 'picking name'},
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
                "name":  'Location foo baz',
            },
            "location_dst": {
                "id": 2,
                "name": 'Location bar',
            },
            "product": {"id": 1, "name": 'product name'},
            "picking": {"id": 1, "name": 'picking name'},
        },
        "state": "scan_location",
        "message": {"message_type": "", "title": "", "body": ""}
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
        "data": undefined,
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
            "location_src": {
                "id": 1,
                "name":  'Location foo baz',
            },
            "location_dst": {
                "id": 2,
                "name": 'Location Benoit',
            },
            "product": {"id": 1, "name": 'product name'},
            "picking": {"id": 1, "name": 'picking name'},
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
var CASE_5 = {
    'fetch' : {
        "data": {
            "id": 1,
            "location_src": {
                "id": 1,
                "name":  'Location foo baz',
            },
            "location_dst": {
                "id": 2,
                "name": 'Location Benoit',
            },
            "product": {"id": 1, "name": 'product name'},
            "picking": {"id": 1, "name": 'picking name'},
        },
        "state": "scan_location",
        "message": undefined
    },
    'validate1' : {
        "data": undefined,
        "state": "confirm_location",
        "message": {"message_type": "warning", "body": "Are you sure of this location?"}
    },
    'validate2' : {
        "data": undefined,
        "state": "scan_pack",
        "message": undefined,
    },
}
var CASE_6 = {
    'fetch' : {
        "data": {
            "id": 1,
            "location_src": {
                "id": 1,
                "name":  'Location foo baz',
            },
            "location_dst": {
                "id": 2,
                "name": 'Location Benoit',
            },
            "product": {"id": 1, "name": 'product name'},
            "picking": {"id": 1, "name": 'picking name'},
        },
        "state": "scan_location",
        "message": undefined
    },
    'validate' : {
        "data": undefined,
        "state": "scan_location",
        "message": {"message_type": "error", "body": "You cannot move to this location"}
    },
}



window.CASES = {
    "1": CASE_1,
    "2": CASE_2,
    "3": CASE_3,
    "4": CASE_4,
    "5": CASE_5,
    "6": CASE_6,
};

window.CASE = window.CASES["1"];