/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
 */

export class BaseRegistry {
    /**
     * Initialize registry as an empty key array.
     */
    constructor() {
        this._data = {};
        this._make_route_path_pattern = null;
        this._profileRequired = false;
    }
    /**
     * Retrieve and existing process
     * @param {*} key
     * @returns Object
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
     * @returns Object
     */
    add(key, component, route, metadata, override = false) {
        if (!_.isEmpty(this._data[key]) && !override) {
            throw "Component already existing: " + key;
        }
        const meta = metadata || {};
        const _route = route || {};
        _.defaults(_route, {
            path: _route.path || this.make_route_path(key),
            meta: {
                requiresProfile: this._profileRequired,
            },
        });
        this._data[key] = {
            key: key,
            component: component,
            metadata: meta,
            route: _route,
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
     * @returns Object
     */
    replace(key, component, metadata) {
        console.log("Replacing component", key);
        return this.add(key, component, {}, metadata, true);
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
     * @returns Object
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
        _.forEach(overrides, function (value, path) {
            _.set(orig_obj, path, value);
        });
    }
    /**
     * Return all process.
     * @returns Object
     */
    all() {
        return this._data;
    }
    /**
     * Generate a route path for given process key.
     *
     * @param {*} key : process's key.
     * @returns String
     */
    make_route_path(key) {
        return _.template(this._make_route_path_pattern || "/${ key }")({key: key});
    }
    /**
     * Retrieve all items that should appear on menu.
     * @param {*} menu_type : string matching a menu type (sidebar, home, all)
     * @returns Array
     */
    for_menu(menu_type = "all") {
        return _.filter(this._data, function (x) {
            return _.result(x, "metadata.menu._type", null) === menu_type;
        }).map(_.property("metadata.menu"));
    }
}
