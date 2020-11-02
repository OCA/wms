/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {translation_registry} from "../services/translation_registry.js";

const messages_en = {
    screen: {
        home: {
            title: "Barcode scanner",
        },
        scan_anything: {
            title: "Scan {what}",
        },
        settings: {
            home: {
                name: "Settings",
                title: "Settings",
            },
            language: {
                name: "Language",
                title: "Select language",
            },
            profile: {
                name: "Profile",
                title: "Select profile",
            },
            fullscreen: {
                enter: "Go fullscreen",
                exit: "Exit fullscreen",
            },
        },
    },
    language: {
        name: {
            English: "English",
            French: "French",
            German: "German",
        },
    },
    btn: {
        back: {
            title: "Back",
        },
        confirm: {
            title: "Confirm",
        },
        ok: {
            title: "Ok",
        },
    },
    picking_type: {
        lines_count: "{lines_count} lines (over {picking_count} operations).",
        priority_lines_count:
            "{priority_lines_count} priority lines (over {priority_picking_count} operations).",
    },
    zone_picking: {
        picking_type_detail: "{lines_count} ({priority_lines_count}) {name}",
    },
    order_lines_by: {
        priority: "Order by priority",
        location: "Order by location",
    },
};

translation_registry.add("en-US", messages_en);
