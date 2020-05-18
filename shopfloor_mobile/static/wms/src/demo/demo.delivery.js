import {demotools} from "./demo.core.js";

const deliver_data = {
    picking: demotools.makePicking({}, {lines_count: 5, line_random_pack: true}),
};

const move_lines = demotools.makePickingLines(
    {},
    {lines_count: 5, line_random_pack: true}
);
// set at least one as done
move_lines[0].qty_done = move_lines[0].quantity;

const picking1 = demotools.makePicking(
    {
        move_lines: move_lines,
    },
    {no_lines: true}
);

const manual_selection_pickings = _.sampleSize([picking1], _.random(1, 8));

const DEMO_DELIVERY = {
    scan_deliver: {
        NOPACK: {
            // No picking
            next_state: "start",
            message: {
                message_type: "error",
                body: "No picking found for PACK1",
            },
        },
        PACK: {
            // All line have a destination pack
            next_state: "deliver",
            data: {
                deliver: deliver_data,
            },
        },
    },
    list_stock_picking: {
        next_state: "manual_selection",
        message: null,
        data: {
            manual_selection: {
                // TODO: simulate completeness for progress bar
                pickings: manual_selection_pickings,
            },
        },
    },
};

demotools.add_case("delivery", DEMO_DELIVERY);
