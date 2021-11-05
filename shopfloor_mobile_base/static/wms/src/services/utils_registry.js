/**
 * Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

export class UtilsRegistry {
    constructor() {
        this._data = {};
    }
    get(key) {
        return this._data[key];
    }
    add(key, value) {
        _.set(this._data, key, value);
    }
    all() {
        return this._data;
    }
}

export var utils_registry = new UtilsRegistry();
