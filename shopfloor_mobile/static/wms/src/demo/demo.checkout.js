/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {demotools} from "/shopfloor_mobile_base/static/wms/src/demo/demo.core.js";

const select_pack_picking = demotools.makePicking(
    {},
    {lines_count: 5, line_random_pack: true, line_random_dest: true}
);

const move_lines1 = demotools.makePickingLines(
    {},
    {lines_count: 5, line_random_pack: true}
);
const select_line_picking = demotools.makePicking(
    {
        move_lines: move_lines1,
    },
    {no_lines: true}
);

const move_lines2 = demotools.makePickingLines(
    {},
    {lines_count: 5, line_random_pack: true}
);
const summary_picking = demotools.makePicking(
    {
        move_lines: move_lines2,
    },
    {no_lines: true}
);

const DEMO_CHECKOUT = {
    scan_document: {
        PACK1: {
            // No picking
            next_state: "select_document",
            message: {
                message_type: "error",
                body: "No picking found for PACK1",
            },
        },
        PACK2: {
            // All line have a destination pack
            next_state: "select_line",
            data: {
                select_line: {picking: select_line_picking},
            },
        },
    },
    select: {
        next_state: "select_line",
        data: {
            select_line: {picking: select_line_picking},
        },
    },
    list_stock_picking: {
        next_state: "manual_selection",
        message: null,
        data: {
            manual_selection: {
                pickings: _.sampleSize(
                    [
                        demotools.makePicking(),
                        demotools.makePicking(),
                        demotools.makePicking(),
                        demotools.makePicking(),
                        demotools.makePicking(),
                        demotools.makePicking(),
                        demotools.makePicking(),
                        demotools.makePicking(),
                    ],
                    _.random(8)
                ),
            },
        },
    },
    select_line: {
        next_state: "select_package",
        data: {
            select_package: {
                picking: select_pack_picking,
                selected_move_lines: select_pack_picking.move_lines,
            },
        },
    },
    select_package: {
        data: {
            select_package: {
                picking: select_pack_picking,
                selected_move_lines: select_pack_picking.move_lines,
            },
        },
    },
    reset_line_qty: {
        next_state: "select_package",
        data: {
            select_package: {
                picking: select_pack_picking,
                // simulate unselecting 1 line
                selected_move_lines: select_pack_picking.move_lines,
            },
        },
    },
    list_dest_package: {
        next_state: "select_dest_package",
        data: {
            select_dest_package: {
                picking: select_pack_picking,
                packages: _.sampleSize(
                    [
                        demotools.makePack(),
                        demotools.makePack(),
                        demotools.makePack(),
                        demotools.makePack(),
                        demotools.makePack(),
                        demotools.makePack(),
                        demotools.makePack(),
                        demotools.makePack(),
                    ],
                    _.random(8)
                ),
                // simulate unselecting 1 line
                selected_move_lines: select_pack_picking.move_lines,
            },
        },
    },
    set_dest_package: {
        next_state: "select_line",
        data: {
            select_line: {picking: select_line_picking},
        },
        message: {
            message_type: "info",
            body: "Product(s) packed in XYZ",
        },
    },
    scan_dest_package: {
        next_state: "select_line",
        data: {
            select_line: {picking: select_line_picking},
        },
        message: {
            message_type: "info",
            body: "Product(s) packed in XYZ",
        },
    },
    new_package: {
        next_state: "select_line",
        data: {
            select_line: {picking: select_line_picking},
        },
        message: {
            message_type: "info",
            body: "Product(s) packed in XYZ",
        },
    },
    no_package: {
        next_state: "select_line",
        data: {
            select_line: {picking: select_line_picking},
        },
        message: {
            message_type: "info",
            body: "Product(s) packed in XYZ",
        },
    },
    summary: {
        next_state: "summary",
        data: {
            summary: {picking: summary_picking},
        },
    },
    remove_package: {
        next_state: "summary",
        data: {
            summary: {picking: summary_picking},
        },
    },
    done: {
        next_state: "select_document",
        message: {
            message_type: "info",
            body: "Done",
        },
    },
    list_packaging: {
        next_state: "change_packaging",
        data: {
            change_packaging: {
                picking: select_pack_picking,
                package: demotools.makePack(),
                packaging: _.sampleSize(
                    [
                        demotools.makePackaging(),
                        demotools.makePackaging(),
                        demotools.makePackaging(),
                        demotools.makePackaging(),
                        demotools.makePackaging(),
                        demotools.makePackaging(),
                        demotools.makePackaging(),
                        demotools.makePackaging(),
                    ],
                    _.random(8)
                ),
            },
        },
    },
    set_packaging: {
        next_state: "summary",
        data: {
            summary: {picking: summary_picking},
        },
        message: {
            message_type: "info",
            body: "Package changed",
        },
    },
    set_custom_qty: {
        next_state: "select_package",
        data: {
            select_package: {
                picking: select_pack_picking,
                // simulate unselecting 1 line
                selected_move_lines: select_pack_picking.move_lines,
            },
        },
        message: {
            message_type: "info",
            body: "Quantity changed",
        },
    },
};

demotools.add_case("checkout", DEMO_CHECKOUT);
