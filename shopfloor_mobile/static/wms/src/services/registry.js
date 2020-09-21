/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

export class Registry {
    constructor() {
        this._data = {};
    }

    get(key) {
        return this._data[key];
    }

    // TODO: document (eg: `component` is just an object not a vuejs component)
    add(key, component, metadata) {
        const meta = metadata || {};
        this._data[key] = {
            key: key,
            component: component,
            metadata: meta,
            path: meta.path || this.make_path(key),
        };
    }

    replace(key, component, metadata) {
        console.log("Replacing process", key);
        return this.add(key, component, metadata);
    }

    all() {
        return this._data;
    }

    make_path(code) {
        return _.template("/${ code }/:menu_id/:state?")({code: code});
    }
}

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

export class TranslationRegistry {
    constructor() {
        this._data = {};
    }

    get(path) {
        return _.result(this._data, path);
    }

    add(path, value) {
        _.set(this._data, path, value);
    }

    all() {
        return this._data;
    }
}
