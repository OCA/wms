import {demotools} from "./demo.core.js";

const deliver_data = {
    picking: demotools.makePicking({}, {lines_count: 5, line_random_pack: true}),
};

let pickings = [];
const count = 8;

for (let i = 1; i < count + 1; i++) {
    const move_lines = demotools.makePickingLines(
        {},
        {lines_count: demotools.getRandomInt(5), line_random_pack: true}
    );
    for (let i = 0; i < demotools.getRandomInt(move_lines.length); i++) {
        // set some as done
        move_lines[i].qty_done = move_lines[i].quantity;
    }
    pickings.push(
        demotools.makePicking(
            {
                move_lines_count: move_lines.length,
                move_lines: move_lines,
            },
            {no_lines: true}
        )
    );
}

const manual_selection_pickings = _.sampleSize(pickings, _.random(1, 8));

let scan_deliver = {};

manual_selection_pickings.forEach(function(p) {
    scan_deliver[p.name] = {
        // All line have a destination pack
        next_state: "deliver",
        data: {
            deliver: {picking: p},
        },
    };
});

const DEMO_DELIVERY = {
    scan_deliver: scan_deliver,
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
