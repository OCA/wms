/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */
import {utils_registry} from "./utils_registry.js";

export class ColorRegistry {
    constructor(theme, _default = "light") {
        this.themes = {};
        this.default_theme = _default;
    }

    add_theme(colors, theme) {
        if (_.isUndefined(theme)) theme = this.default_theme;
        this.themes[theme] = colors;
    }

    color_for(key, theme) {
        if (_.isUndefined(theme)) theme = this.default_theme;
        if (!this.themes[theme]) {
            console.log("Theme", theme, "not registered.");
            return null;
        }
        return this.themes[theme][key];
    }

    get_themes() {
        return this.themes;
    }
}

export var color_registry = new ColorRegistry();

utils_registry.add("colors", color_registry);

color_registry.add_theme(
    {
        /**
         * Standard keys
         */
        primary: "#491966",
        secondary: "#CFD2FF",
        accent: "#82B1FF",
        error: "#c22a4a",
        info: "#5e60ab",
        success: "#8fbf44",
        // Warning: "#FFC107",
        warning: "#e5ab00",
        /**
         * App specific
         */
        content_bg: "grey lighten-3",
        screen_step_done: "#8fbf44",
        screen_step_todo: "#FFE3AC",
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
        /**
         * Spinner
         */
        spinner: "#491966",
        /**
         * Details
         */
        detail_main_card: "info lighten-4",
        detail_main_card_selected: "rgba(3, 215, 252, 1)",
        /**
         * detail_simple_product
         */
        pack_line_done: "#5cff87",
        pack_line_selected: "#d8c45c",
        pack_line_filled: "rgba(162, 121, 0, 0.84)",
        quantity_done: "rgba(162, 121, 0, 0.33)",
    },
    "light"
); // TODO: we should bave a theme named "coosa" and select it
