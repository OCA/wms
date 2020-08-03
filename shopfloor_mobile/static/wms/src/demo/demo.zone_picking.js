import {demotools} from "./demo.core.js";

const DEMO_CASE = {
    by_menu_id: {},
};

const zone_picking_menu_case1 = demotools.addAppMenu(
    {
        name: "Zone picking: case 1",
        scenario: "zone_picking",
        picking_types: [{id: 27, name: "Random type"}],
    },
    "zp_1"
);

function _makePickingType() {
    return demotools.makePickingType({
        lines_count: demotools.getRandomInt(10),
        picking_count: demotools.getRandomInt(10),
        priority_lines_count: demotools.getRandomInt(10),
        priority_picking_count: demotools.getRandomInt(10),
        code: "internal",
    });
}

const pick_type1 = _makePickingType();
const pick_type2 = _makePickingType();
const pick_type3 = _makePickingType();
const pick_type4 = _makePickingType();

const scan_location_picking_types = _.sampleSize(
    [pick_type1, pick_type2, pick_type3, pick_type4],
    demotools.getRandomInt(4)
);

const move_lines = demotools.makePickingLines(
    {},
    {lines_count: 30, line_random_pack: true, picking_auto: true}
);
const select_line_move_lines = _.orderBy(move_lines, ["priority"], ["desc"]);

const list_move_lines = {
    next_state: "select_line",
    data: {
        select_line: {
            zone_location: demotools.makeLocation(),
            picking_type: _.cloneDeep(_.sample(scan_location_picking_types)),
            move_lines: select_line_move_lines,
        },
    },
};

const unload_all_data = {
    zone_location: demotools.makeLocation(),
    picking_type: _.cloneDeep(list_move_lines.data.select_line.picking_type),
    move_lines: _.cloneDeep(select_line_move_lines),
};

const unload_set_destination_data = {
    zone_location: demotools.makeLocation(),
    picking_type: _.cloneDeep(list_move_lines.data.select_line.picking_type),
    move_line: _.cloneDeep(select_line_move_lines[0]),
    full_order_picking: true,
};

const DEMO_CASE_1 = {
    scan_location: {
        next_state: "select_picking_type",
        data: {
            select_picking_type: {
                zone_location: demotools.makeLocation(),
                picking_types: _.cloneDeep(scan_location_picking_types),
            },
        },
    },
    list_move_lines: function(data) {
        let res = _.cloneDeep(list_move_lines);
        if (data.order == "location") {
            res.data.select_line.move_lines = _.orderBy(
                res.data.select_line.move_lines,
                ["location_src.name"]
            );
        } else {
            res.data.select_line.move_lines = _.orderBy(
                res.data.select_line.move_lines,
                ["priority"],
                ["desc"]
            );
        }
        return res;
    },
    scan_source: {
        next_state: "set_line_destination",
        data: {
            set_line_destination: {
                zone_location: demotools.makeLocation(),
                picking_type: _.cloneDeep(
                    list_move_lines.data.select_line.picking_type
                ),
                move_line: _.cloneDeep(select_line_move_lines[0]),
            },
        },
    },
    set_destination: {
        next_state: "select_line",
        message: {
            message_type: "success",
            body: "Item moved",
        },
        data: {
            select_line: {
                zone_location: demotools.makeLocation(),
                picking_type: _.cloneDeep(
                    list_move_lines.data.select_line.picking_type
                ),
                move_lines: _.cloneDeep(select_line_move_lines),
            },
        },
    },
    prepare_unload: {
        next_state: "unload_all",
        data: {
            unload_all: _.cloneDeep(unload_all_data),
        },
    },
    stock_issue: {
        next_state: "select_line",
        message: {
            message_type: "success",
            body: "Stock out confirmed",
        },
        data: {
            select_line: _.cloneDeep(list_move_lines.data.select_line),
        },
    },
    is_zero: {
        next_state: "select_line",
        message: {
            message_type: "success",
            body: "Stock zero confirmed",
        },
        data: {
            select_line: _.cloneDeep(list_move_lines.data.select_line),
        },
    },
    set_destination_all: function(data) {
        if (!data.confirmation) {
            const _data = _.extend(_.cloneDeep(unload_all_data), {
                confirmation_required: true,
            });
            return {
                next_state: "unload_all",
                data: {
                    unload_all: _data,
                },
                message: {
                    message_type: "warning",
                    body: "Confirm you want to unload them all?",
                },
            };
        } else {
            return {
                next_state: "select_line",
                message: {
                    message_type: "success",
                    body: "All lines moved",
                },
                data: {
                    select_line: _.cloneDeep(list_move_lines.data.select_line),
                },
            };
        }
    },
    change_pack_lot: {
        next_state: "set_line_destination",
        data: {
            set_line_destination: {
                zone_location: demotools.makeLocation(),
                picking_type: _.cloneDeep(
                    list_move_lines.data.select_line.picking_type
                ),
                move_line: _.cloneDeep(select_line_move_lines[0]),
            },
        },
    },
    unload_split: {
        next_state: "unload_single",
        data: {
            unload_single: {
                zone_location: demotools.makeLocation(),
                picking_type: _.cloneDeep(
                    list_move_lines.data.select_line.picking_type
                ),
                move_line: _.cloneDeep(select_line_move_lines[0]),
                full_order_picking: true,
            },
        },
    },
    unload_scan_pack: {
        next_state: "unload_set_destination",
        data: {
            unload_set_destination: unload_set_destination_data,
        },
    },
    unload_scan_destination: function(data) {
        if (!data.confirmation) {
            const _data = _.extend(_.cloneDeep(unload_set_destination_data), {
                confirmation_required: true,
            });
            return {
                next_state: "unload_set_destination",
                data: {
                    unload_set_destination: _data,
                },
                message: {
                    message_type: "warning",
                    body: "Confirm you want to unload them all?",
                },
            };
        } else {
            return {
                next_state: "select_line",
                message: {
                    message_type: "success",
                    body: "All lines moved",
                },
                data: {
                    select_line: _.cloneDeep(list_move_lines.data.select_line),
                },
            };
        }
    },
};

DEMO_CASE.by_menu_id[zone_picking_menu_case1] = DEMO_CASE_1;

demotools.add_case("zone_picking", DEMO_CASE);
