/* eslint no-use-before-define: 0 */ // --> OFF
var CANCEL_MSG_DEFAULT = {
    message: "Operation cancelled",
    message_type: "info",
};

var DEMO_SINGLE_PUTAWAY_1 = {
    start: {
        data: {
            scan_location: {
                id: 1,
                name: "A nice pack 1",
                location_src: {
                    id: 1,
                    name: "Location SRC 1",
                },
                location_dest: {
                    id: 2,
                    name: "Location SRC 2",
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
        next_state: "start_scan_pack",
        message: {
            message: "Pack validated",
            message_type: "success",
        },
    },
    cancel: {
        next_state: "start",
        message: CANCEL_MSG_DEFAULT,
    },
};

var DEMO_SINGLE_PUTAWAY_2 = {
    start: {
        data: undefined,
        next_state: "start_scan_pack",
        message: {message_type: "error", message: "You cannot do that!"},
    },
};
var DEMO_SINGLE_PUTAWAY_3 = {
    start: {
        data: undefined,
        next_state: "start_scan_pack",
        message: {message_type: "error", message: "No pkg found"},
    },
};
var DEMO_SINGLE_PUTAWAY_4 = {
    start: {
        data: {
            confirm_start: {
                id: 1,
                name: "A nice pack 4",
                location_src: {
                    id: 1,
                    name: "Location SRC 4",
                },
                location_dest: {
                    id: 2,
                    name: "Location DST 4",
                },
                product: {id: 1, name: "Product 4"},
                picking: {id: 1, name: "Picking 4"},
            },
        },
        next_state: "confirm_start",
        message: {
            message_type: "info",
            message: "Benoit is at the toilette: do you take over?",
        },
    },
    validate: {
        data: undefined,
        next_state: "start_scan_pack",
        message: {
            message: "Pack validated",
            message_type: "success",
        },
    },
    cancel: {
        next_state: "start",
        message: CANCEL_MSG_DEFAULT,
    },
};
var DEMO_SINGLE_PUTAWAY_5 = {
    start: {
        data: {
            scan_location: {
                id: 1,
                name: "A nice pack 5",
                location_src: {
                    id: 1,
                    name: "Location SRC 5",
                },
                location_dest: {
                    id: 2,
                    name: "Location DST 5",
                },
                product: {id: 1, name: "Product 5"},
                picking: {id: 1, name: "Picking 5"},
            },
        },
        next_state: "scan_location",
        message: undefined,
    },
    cancel: {
        next_state: "start",
        message: CANCEL_MSG_DEFAULT,
    },
    validate: {
        data: undefined,
        next_state: "start_scan_pack",
        message: {
            message: "Pack validated",
            message_type: "success",
        },
    },
};
var DEMO_SINGLE_PUTAWAY_6 = {
    start: {
        data: {
            scan_location: {
                id: 1,
                name: "A nice pack 6",
                location_src: {
                    id: 1,
                    name: "Location SRC 6",
                },
                location_dest: {
                    id: 2,
                    name: "Location DST 6",
                },
                product: {id: 1, name: "Product 6"},
                picking: {id: 1, name: "Picking 6"},
            },
        },
        next_state: "scan_location",
        message: undefined,
    },
    validate: {
        data: undefined,
        next_state: "confirm_location",
        message: {message_type: "warning", message: "Are you sure of this location?"},
    },
    LOC6: {
        data: undefined,
        next_state: "start_scan_pack",
        message: {
            message: "Pack validated",
            message_type: "success",
        },
    },
};
var DEMO_SINGLE_PUTAWAY_7 = {
    start: {
        data: {
            scan_location: {
                id: 1,
                name: "A nice pack 7",
                location_src: {
                    id: 1,
                    name: "Location SRC 7",
                },
                location_dest: {
                    id: 2,
                    name: "Location DST 7",
                },
                product: {id: 1, name: "Product 7"},
                picking: {id: 1, name: "Picking 7"},
            },
        },
        next_state: "scan_location",
        message: undefined,
    },
    validate: {
        data: undefined,
        next_state: "scan_location",
        message: {message_type: "error", message: "You cannot move to this location"},
    },
    LOC7: {
        data: undefined,
        next_state: "start_scan_pack",
        message: {
            message: "Pack validated",
            message_type: "success",
        },
    },
};

window.DEMO_CASES.single_pack_putaway = {
    "1": DEMO_SINGLE_PUTAWAY_1,
    "2": DEMO_SINGLE_PUTAWAY_2,
    "3": DEMO_SINGLE_PUTAWAY_3,
    "4": DEMO_SINGLE_PUTAWAY_4,
    "5": DEMO_SINGLE_PUTAWAY_5,
    "6": DEMO_SINGLE_PUTAWAY_6,
    "7": DEMO_SINGLE_PUTAWAY_7,
};

/* eslint no-use-before-define: 2 */ // --> ON
