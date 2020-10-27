/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ColorRegistry} from "./registry.js";

export var color_registry = new ColorRegistry();

color_registry.add_theme(
    {
        /**
         * standard keys
         */
        primary: "#491966",
        secondary: "#CFD2FF",
        accent: "#82B1FF",
        error: "#c22a4a",
        info: "#5e60ab",
        success: "#8fbf44",
        // warning: "#FFC107",
        warning: "#e5ab00",
        /**
         * app specific
         */
        content_bg: "grey lighten-3",
        screen_step_done: "#8fbf44",
        screen_step_todo: "#FFE3AC",
        /**
         * icons
         */
        info_icon: "info darken-2",
        /**
         * buttons / actions
         */
        btn_action: "primary lighten-2",
        btn_action_cancel: "error",
        btn_action_warn: "warning",
        btn_action_complete: "success",
        btn_action_todo: "screen_step_todo",
        btn_action_back: "info lighten-1",
        /**
         * selection
         */
        item_selected: "success",
        /**
         * spinner
         */
        spinner: "#491966",
        /**
         * details
         */
        detail_main_card: "info lighten-4",
    },
    "light"
); // TODO: we should bave a theme named "coosa" and select it
