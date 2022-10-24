/**
 * Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
 */

import {demotools} from "/shopfloor_mobile_base/static/wms/src/demo/demo.core.js";

const DEMO_CASE = {
    by_menu_id: {},
};

let receipt_pickings = [];
for (let i = 0; i < 10; i++) {
    receipt_pickings.push(
        demotools.makePicking(
            {},
            {lines_count: 5, line_random_pack: true, line_random_dest: true}
        )
    );
}

const data_for_select_document = {
    next_state: "select_document",
    data: {
        select_document: {
            pickings: receipt_pickings,
        },
    },
};

const reception_menu_case1 = demotools.addAppMenu(
    {
        name: "Reception",
        scenario: "reception",
        picking_types: [{id: 27, name: "Random type"}],
    },
    "re_1"
);

const DEMO_RECEPTION = {
    receipts: function (data) {
        const res = data_for_select_document;
        return res;
    },
    scan_document: function (data) {
        return {
            next_state: "select_line",
            data: {
                select_line: {
                    picking: receipt_pickings.find((p) => p.id === data.picking_id),
                },
            },
        };
    },
};

DEMO_CASE.by_menu_id[reception_menu_case1] = DEMO_RECEPTION;

demotools.add_case("reception", DEMO_CASE);
