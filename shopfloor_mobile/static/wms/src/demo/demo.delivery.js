/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {demotools} from "/shopfloor_mobile_base/static/wms/src/demo/demo.core.js";

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
                pickings: manual_selection_pickings,
            },
        },
    },
    // TODO: it would be nice if we can define handlers to modify demo data
    // in "real way".
    reset_qty_done_pack: {
        next_state: "deliver",
        message: {
            body: "Qty reset done",
        },
        data: {
            deliver: {picking: _.values(scan_deliver)[0]},
        },
    },
    reset_qty_done_line: {
        next_state: "deliver",
        message: {
            body: "Qty reset done",
        },
        data: {
            deliver: {picking: _.values(scan_deliver)[0]},
        },
    },
};

demotools.add_case("delivery", DEMO_DELIVERY);
