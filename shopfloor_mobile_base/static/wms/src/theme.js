/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
 */
import {color_registry} from "./services/color_registry.js";

const error_color = "#c22a4a";
const success_color = "#8fbf44";
const accent_color = "#82B1FF";
const info_color = "#5e60ab";
const warning_color = "#e5ab00";
const todo_color = "#FFE3AC";

color_registry.add_theme(
    {
        /**
         * Standard keys
         */
        primary: "#491966",
        secondary: "#CFD2FF",
        accent: accent_color,
        error: error_color,
        info: info_color,
        success: success_color,
        // Warning: "#FFC107",
        warning: warning_color,
        /**
         * App specific
         */
        content_bg: "grey lighten-3",
        screen_step_done: success_color,
        screen_step_todo: todo_color,
        /**
         * Icons
         */
        info_icon: "info darken-2",
        /**
         * Buttons / actions
         */
        btn_action: "primary lighten-2",
        btn_action_cancel: "error",
        btn_action_warn: "warning",
        btn_action_complete: "success",
        btn_action_todo: "screen_step_todo",
        btn_action_back: "info lighten-1",
        /**
         * Selection
         */
        item_selected: "success",
        item_selected_partial: "warning",
        item_selected_excess: "error",
        /**
         * Spinner
         */
        spinner: "dark_green",
        /**
         * Details
         */
        detail_main_card: "info lighten-4",
    },
    "light"
);
