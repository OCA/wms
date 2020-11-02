/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

/**
 * A "process" represents a barcode app process (eg: pick goods for reception).
 *
 * A process registry is responsible for collecting all the processes
 * and ease their registration, lookup and override.
 *
 * The router will use this registry to register processes routes.
 */
export class ProcessRegistry {
    /**
     * Initialize registry as an empty key array.
     */
    constructor() {
        this._data = {};
    }

    /**
     * Retrieve and existing process
     * @param {*} key
     */
    get(key) {
        return this._data[key];
    }
    /**
     * Register a new process.
     *
     * @param {*} key : the unique key
     * @param {*} component : the component plain Object.
     * This should be a bare JS object and not a Vue component
     * so that it gets registered locally in the app.
     * @param {*} metadata : additional information for the process.
     * Eg: `path` is used to override automatic computation of the route path.
     * @param {*} override : bypass validation for existing process.
     */
    add(key, component, metadata, override = false) {
        if (!_.isEmpty(this._data[key]) && !override) {
            throw "Component already existing: " + key;
        }
        const meta = metadata || {};
        this._data[key] = {
            key: key,
            component: component,
            metadata: meta,
            path: meta.path || this.make_path(key),
        };
        return this._data[key];
    }
    /**
     * Replace an existing process.
     *
     * @param {*} key : the unique key
     * @param {*} component : the component plain Object.
     * This should be a bare JS object and not a Vue component
     * so that it gets registered locally in the app.
     * @param {*} metadata : additional information for the process.
     */
    replace(key, component, metadata) {
        console.log("Replacing process", key);
        return this.add(key, component, metadata, true);
    }
    /**
     * Extend an existing process.
     *
     * @param {*} key : the unique key
     * @param {*} component_override : the component plain Object.
     * This should be a bare JS object and not a Vue component
     * so that it gets registered locally in the app.
     *
     * Keys can be Lodash-like paths to the destination keys to override.
     * Eg: {"methods.foo": function() { alert("foo")}}
     * will override the VueJS component method called "foo".
     */
    extend(key, component_override) {
        const original = this.get(key);
        if (_.isEmpty(original)) {
            throw "Component not found: " + key;
        }
        const new_component = Object.create(original.component);
        this._override(new_component, component_override);
        return new_component;
    }
    /**
     * Override original object properties with given overrides
     * @param {*} orig_obj : JS object
     * @param {*} overrides : JS object
     *
     * Keys can be Lodash-like paths to the destination keys to override.
     */
    _override(orig_obj, overrides) {
        _.forEach(overrides, function(value, path) {
            _.set(orig_obj, path, value);
        });
    }
    /**
     * Return all process.
     */
    all() {
        return this._data;
    }
    /**
     * Generate a route path for given process key.
     *
     * @param {*} key : process's key.
     */
    make_path(key) {
        return _.template("/${ key }/:menu_id/:state?")({key: key});
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
        this._default_lang = "en-US";
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

    available_langs() {
        return Object.keys(this._data);
    }

    set_default_lang(lang) {
        if (_.isEmpty(this._data[lang])) {
            throw "Language not available: " + lang;
        }
        this._default_lang = lang;
    }

    get_default_lang() {
        return this._default_lang;
    }
}
