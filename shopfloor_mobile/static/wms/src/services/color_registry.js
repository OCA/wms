import {ColorRegistry} from "./registry.js";

export var color_registry = new ColorRegistry();

color_registry.add_theme({
    screen_step_done: "green accent-4",
    screen_step_todo: "amber",
});
