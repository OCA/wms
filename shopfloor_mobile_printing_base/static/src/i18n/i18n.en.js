/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
 */

import {translation_registry} from "../services/translation_registry.js";

const messages_en = {
    screen: {
        login: {
            title: "Login",
            action: {
                login: "Login",
            },
            error: {
                login_invalid: "Login failed. Invalid credentials",
            },
        },
        home: {
            title: "Home",
            main_title: "Home",
            version: "Version:",
            action: {
                nuke_data_and_reload: "Force reload data and refresh",
            },
        },
        scan_anything: {
            name: "Scan",
            title: "Scan {what}",
            scan_placeholder: "Scan anything",
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
        action: {
            logout: "Logout",
        },
        nav: {
            scenario: "Scenario:",
            op_types: "Op Types:",
        },
        log_entry_link: "View / share log entry",
        running_env: {
            prod: "Production",
            integration: "Integration",
            staging: "Staging",
            test: "Test",
            dev: "Development",
        },
        report_issue: {
            action_txt: "Need help?",
            mail: {
                subject: "I need help with the {app_name} app",
                info_warning_msg: "PLEASE, DO NOT ALTER THE INFO BELOW",
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
        // TODO: split out WMS messages
        btn_get_work: "Get work",
        btn_manual_selection: "Manual selection",
        stock_zero_check: {
            confirm_stock_zero: "Confirm stock = 0",
            confirm_stock_not_zero: "Declare stock not empty",
        },
        actions_popup: {
            btn_action: "Action",
        },
        lines_count: "{priority_lines_count}/{lines_count}",
        lines_count_extended: "{priority_lines_count}/{lines_count} position(s)",
        picking_count: "{priority_picking_count}/{picking_count}",
        picking_count_extended: "{priority_picking_count}/{picking_count} picking(s)",
    },
    list: {
        no_items: "No item to list.",
    },
    select: {
        no_items: "No item to select.",
    },
    order_lines_by: {
        priority: "Order by priority",
        location: "Order by location",
    },
};

translation_registry.add("en-US", messages_en);
