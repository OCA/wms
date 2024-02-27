/**
 * Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
 * @author Simone Orsi <simahawk@gmail.com>
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
 */

export class AuthHandlerMixin {
    constructor($root) {
        this.$root = $root;
    }
    get_params() {
        return {};
    }
    get_login_component_name() {
        return "login-" + this.$root.app_info.auth_type;
    }
    // TODO: document on_login and on_logout
}

/**
 * Hold authentication handlers.
 */
export class AuthHandlerRegistry {
    constructor() {
        this._data = {};
    }
    get(auth_type) {
        return this._data[auth_type];
    }
    add(auth_type, handler) {
        this._data[auth_type] = handler;
    }
}

export var auth_handler_registry = new AuthHandlerRegistry();
