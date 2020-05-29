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
        warning: "amber",
        /**
         * app specific
         */
        screen_step_done: "success",
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
        btn_action_warn: "amber",
        btn_action_complete: "success",
        /**
         * selection
         */
        item_selected: "success",
    },
    "light"
); // TODO: we should bave a theme named "coosa" and select it
