/**
 * Copyright 2023 Camptocamp SA
 * @author Simone Orsi <simahawk@gmail.com>
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
 */

/**
 * Global actions registry.
 *
 * Register action components to be used by specific UI components.
 *
 * For an example, check `app-bar-action-scan-anything`.
 *
 */
export class ActionsRegistry {
    constructor() {
        this._data = {};
    }
    get(key) {
        return this._data[key];
    }
    add(key, value) {
        _.set(this._data, key, value);
    }
    /**
     * Retrieve all actions matching given tag sorted by sequence.
     *
     * @param {String} tag: tag to filter with
     */
    by_tag(tag) {
        return _.filter(this._data, function (x) {
            return x.tag == tag;
        }).sort((current, next) => current.sequence - next.sequence);
    }
}

export var actions_registry = new ActionsRegistry();
