import {demotools} from "./demo.core.js";

// TODO: refactor w/ demotools data

const CANCEL_MSG_DEFAULT = {
    message: "Operation cancelled",
    message_type: "info",
};

const DEMO_SINGLE_PUTAWAY_1 = {
    start: {
        data: {
            scan_location: demotools.makeSingleLineOperation(),
        },
        next_state: "scan_location",
    },
    validate: {
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

const DEMO_SINGLE_PUTAWAY_2 = {
    start: {
        next_state: "start_scan_pack",
        message: {message_type: "error", message: "You cannot do that!"},
    },
};
const DEMO_SINGLE_PUTAWAY_3 = {
    start: {
        next_state: "start_scan_pack",
        message: {message_type: "error", message: "No pkg found"},
    },
};
const DEMO_SINGLE_PUTAWAY_4 = {
    start: {
        data: {
            confirm_start: demotools.makeSingleLineOperation(),
        },
        next_state: "confirm_start",
        message: {
            message_type: "info",
            message: "Benoit is at the toilette: do you take over?",
        },
    },
    validate: {
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
const DEMO_SINGLE_PUTAWAY_5 = {
    start: {
        data: {
            scan_location: demotools.makeSingleLineOperation(),
        },
        next_state: "scan_location",
    },
    cancel: {
        next_state: "start",
        message: CANCEL_MSG_DEFAULT,
    },
    validate: {
        next_state: "start_scan_pack",
        message: {
            message: "Pack validated",
            message_type: "success",
        },
    },
};
const DEMO_SINGLE_PUTAWAY_6 = {
    start: {
        data: {
            scan_location: demotools.makeSingleLineOperation(),
        },
        next_state: "scan_location",
    },
    validate: {
        next_state: "confirm_location",
        message: {message_type: "warning", message: "Are you sure of this location?"},
    },
    LOC6: {
        next_state: "start_scan_pack",
        message: {
            message: "Pack validated",
            message_type: "success",
        },
    },
};
const DEMO_SINGLE_PUTAWAY_7 = {
    start: {
        data: {
            scan_location: demotools.makeSingleLineOperation(),
        },
        next_state: "scan_location",
    },
    validate: {
        next_state: "scan_location",
        message: {message_type: "error", message: "You cannot move to this location"},
    },
    LOC7: {
        next_state: "start_scan_pack",
        message: {
            message: "Pack validated",
            message_type: "success",
        },
    },
};

demotools.add_case("single_pack_putaway", {
    "1": DEMO_SINGLE_PUTAWAY_1,
    "2": DEMO_SINGLE_PUTAWAY_2,
    "3": DEMO_SINGLE_PUTAWAY_3,
    "4": DEMO_SINGLE_PUTAWAY_4,
    "5": DEMO_SINGLE_PUTAWAY_5,
    "6": DEMO_SINGLE_PUTAWAY_6,
    "7": DEMO_SINGLE_PUTAWAY_7,
});
