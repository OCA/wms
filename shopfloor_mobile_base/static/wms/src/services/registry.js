/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
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
     */
    replace(key, component, metadata) {
        console.log("Replacing component", key);
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
    make_route_path(key) {
        return _.template(this._make_route_path_pattern || "/${ key }")({key: key});
    }
}
