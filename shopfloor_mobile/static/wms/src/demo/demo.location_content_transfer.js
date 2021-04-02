/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {demotools} from "/shopfloor_mobile_base/static/wms/src/demo/demo.core.js";

const DEMO_CASE = {
    by_menu_id: {},
};

// Case for recover existing work on single move line
const recover_single_move_line_menu_id = demotools.addAppMenu({
    name: "Loc.Cont.Transfer: recover single line",
    scenario: "location_content_transfer",
    picking_types: [{id: 27, name: "Random type"}],
});
const single_line_case_move_line = demotools.makeSingleLineOperation();
const RECOVER_SINGLE_MOVE_LINE_CASE = {
    start_or_recover: {
        next_state: "start_single",
        message: {
            message_type: "info",
            body: "Recovered line from previous session.",
        },
        data: {
            start_single: {
                recovered: true,
                move_line: _.cloneDeep(single_line_case_move_line),
            },
        },
    },
    scan_line: {
        next_state: "scan_destination",
        message: {
            message_type: "info",
            body: "Recovered line from previous session.",
        },
        data: {
            scan_destination: {
                move_line: _.cloneDeep(single_line_case_move_line),
            },
        },
    },
    set_destination_line: {
        next_state: "start_single",
        message: {
            message_type: "info",
            body: "Destination set on the line",
        },
        data: {
            start_single: {
                move_line: _.cloneDeep(single_line_case_move_line),
            },
        },
    },
};
DEMO_CASE.by_menu_id[recover_single_move_line_menu_id] = RECOVER_SINGLE_MOVE_LINE_CASE;

// Case for recover existing work on single package level
const recover_single_package_level_menu_id = demotools.addAppMenu({
    name: "Loc.Cont.Transfer: recover single package level",
    scenario: "location_content_transfer",
    picking_types: [{id: 27, name: "Random type"}],
});

const single_line_package_level = demotools.makePackageLevel();
const RECOVER_SINGLE_PACKAGE_LEVEL_CASE = {
    start_or_recover: {
        next_state: "start_single",
        message: {
            message_type: "info",
            body: "Recovered package from previous session.",
        },
        data: {
            start_single: {
                recovered: true,
                package_level: _.cloneDeep(single_line_package_level),
            },
        },
    },
    scan_line: {
        next_state: "scan_destination",
        message: {
            message_type: "info",
            body: "Recovered package from previous session.",
        },
        data: {
            scan_destination: {
                package_level: _.cloneDeep(single_line_package_level),
            },
        },
    },
    set_destination_line: {
        next_state: "start_single",
        message: {
            message_type: "info",
            body: "Destination set on the line",
        },
        data: {
            start_single: {
                package_level: _.cloneDeep(single_line_package_level),
            },
        },
    },
};
DEMO_CASE.by_menu_id[
    recover_single_package_level_menu_id
] = RECOVER_SINGLE_PACKAGE_LEVEL_CASE;

// Case for recover existing work on several lines from the same location
const recover_move_lines_same_location_menu_id = demotools.addAppMenu({
    name: "Loc.Cont.Transfer: recover lines same loc.",
    scenario: "location_content_transfer",
    picking_types: [{id: 27, name: "Random type"}],
});
const same_location = demotools.makeLocation();
const scan_destination_all_move_lines = demotools.makePickingLines(
    {},
    {lines_count: demotools.getRandomInt(5), line_random_pack: true}
);
for (let i = 0; i < scan_destination_all_move_lines.length; i++) {
    // set same location (clone to avoid circular dep on storage)
    scan_destination_all_move_lines[i].location_src = _.cloneDeep(same_location);
}
const RECOVER_MOVE_LINES_SAME_LOCATION_CASE = {
    start_or_recover: {
        next_state: "scan_destination_all",
        message: {
            message_type: "info",
            body: "Recovered lines from previous session.",
        },
        data: {
            scan_destination_all: {
                recovered: true,
                move_lines: _.cloneDeep(scan_destination_all_move_lines),
            },
        },
    },
    scan_line: {
        next_state: "scan_destination",
        message: {
            message_type: "info",
            body: "Recovered line from previous session.",
        },
        data: {
            scan_destination: {
                move_lines: _.cloneDeep(scan_destination_all_move_lines),
            },
        },
    },
    set_destination_all: {
        next_state: "start",
        message: {
            message_type: "info",
            body: "Destination set on all lines",
        },
        data: {
            start: {},
        },
    },
    go_to_single: {
        next_state: "start_single",
        data: {
            start_single: {
                move_line: _.cloneDeep(scan_destination_all_move_lines[0]),
            },
        },
    },
};
DEMO_CASE.by_menu_id[
    recover_move_lines_same_location_menu_id
] = RECOVER_MOVE_LINES_SAME_LOCATION_CASE;

demotools.add_case("location_content_transfer", DEMO_CASE);
