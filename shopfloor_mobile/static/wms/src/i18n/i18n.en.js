/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {translation_registry} from "../services/translation_registry.js";

const messages_en = {
    screen: {
        login: {
            title: "Login",
            api_key_placeholder: "YOUR_API_KEY_HERE",
            action: {
                login: "Login",
            },
            error: {
                api_key_invalid: "Invalid API KEY",
            },
        },
        home: {
            title: "Home",
            main_title: "Barcode scanner",
            version: "Version:",
            action: {
                nuke_data_and_reload: "Force reload data and refresh",
            },
        },
        scan_anything: {
            title: "Scan {what}",
        },
        settings: {
            title: "Settings",
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
                profile_updated: "Profile updated",
                action: {
                    logout: "Logout",
                },
            },
            fullscreen: {
                enter: "Go fullscreen",
                exit: "Exit fullscreen",
            },
        },
    },
    app: {
        profile_not_configured: "Profile not configured yet. Please select one.",
        profile_configure: "Configure profile",
        loading: "Loading...",
        nav: {
            scenario: "Scenario:",
            op_types: "Op Types:",
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
        reset: {
            title: "Reset",
        },
        cancel: {
            title: "Cancel",
        },
        reload_config: {
            title: "Reload config and menu",
        },
    },
    misc: {
        btn_get_work: "Get work",
        btn_manual_selection: "Manual selection",
        stock_zero_check: {
            confirm_stock_zero: "Confirm stock = 0",
            confirm_stock_not_zero: "Confirm stock not empty",
        },
        actions_popup: {
            btn_action: "Action",
        },
        lines_count: "{priority_lines_count}/{lines_count}",
        lines_count_extended: "{priority_lines_count}/{lines_count} position(s)",
        picking_count: "{priority_picking_count}/{picking_count}",
        picking_count_extended: "{priority_picking_count}/{picking_count} picking(s)",
    },
    order_lines_by: {
        priority: "Order by priority",
        location: "Order by location",
    },
};

translation_registry.add("en-US", messages_en);
