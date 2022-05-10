/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
 */
import {demotools} from "../demo/demo.core.js";

export class OdooMixin {
    constructor(params) {
        this.params = params;
        this.base_url = params.base_url;
        this.usage = params.usage;
        this.headers = params.headers || {};
        this.debug = this.params.debug;
        // Bypass "loading" state when calling Odoo
        this.in_background = this.params.in_background;
    }
    call(path, data, method = "POST", fullpath = false) {
        const endpoint_info = this._make_endpoint_info(path, fullpath);
        return this._call(endpoint_info, method, data);
    }
    post(path, data, fullpath = false) {
        if (_.isArray(path)) {
            path = path.join("/");
        }
        const endpoint_info = this._make_endpoint_info(path, fullpath);
        return this._call(endpoint_info, "POST", data);
    }
    get(path, data, fullpath = false) {
        if (_.isArray(path)) {
            path = path.join("/");
        }
        const endpoint_info = this._make_endpoint_info(path, fullpath);
        return this._call(endpoint_info, "GET", data);
    }
    _make_endpoint_info(path, fullpath) {
        return {
            endpoint: fullpath ? path : this.usage + "/" + path,
            path: path,
            fullpath: fullpath,
        };
    }
    _call(endpoint_info, method, data) {
        let endpoint = endpoint_info.endpoint;
        if (this.debug) {
            console.log("DEBUG CALL", endpoint);
        }
        const self = this;
        const params = {
            method: method,
            headers: this._get_headers(method),
        };
        data = _.isEmpty(data) ? {} : data;
        if (method == "GET") {
            endpoint += "?" + new URLSearchParams(data).toString();
        } else if (method == "POST") {
            params.body = JSON.stringify(data);
        }
        const fn = this.in_background ? window.standardFetch : window.fetch;
        return fn(this._get_url(endpoint), params).then((response) => {
            if (!response.ok) {
                let handler = self["_handle_" + response.status.toString()];
                if (_.isUndefined(handler)) {
                    handler = this._handle_error;
                }
                return response.json().then((json) => {
                    return {error: handler.call(this, response, json)};
                });
            }
            return response.json();
        });
    }
    _error_info(response, json) {
        return _.extend({}, json, {
            // Strip html
            description: $(json.description).text(),
            // TODO: this might be superfluous as we get error data wrapper by rest api
            error: response.statusText,
            status: response.status,
            response: response,
        });
    }
    _handle_404(response, json) {
        console.log(
            "Endpoint not found, please check your odoo configuration. URL: ",
            response.url
        );
        return this._error_info(response, json);
    }
    _handle_error(response, json) {
        console.log(response.status, response.statusText, response.url);
        return this._error_info(response, json);
    }
    _get_headers(method) {
        let headers = {};
        if (method == "POST") {
            headers["Content-Type"] = "application/json";
        }
        if (!_.isEmpty(this.headers)) {
            _.merge(headers, this.headers);
        }
        return headers;
    }
    _get_url(endpoint) {
        return this.base_url + endpoint;
    }
    _update_headers(headers) {
        _.merge(this.headers, headers);
    }
}

/**
 * The real class to initialize to talk w/ Odoo.
 */
export class Odoo extends OdooMixin {}

/**
 * Mocked Odoo class to use demo data only, no interaction w/ Odoo instance.
 */
// TODO: move this to its on file in demo folder
export class OdooMocked extends OdooMixin {
    constructor(params) {
        super(params);
        this.process_menu_id = this.params.headers["SERVICE-CTX-MENU-ID"];
    }
    _set_demo_data() {
        this.demo_data = demotools.get_case(this.usage);
    }
    _call(endpoint_info, method, data) {
        let path = endpoint_info.path;
        this._set_demo_data();
        console.log("CALL:", path, this.usage);
        console.dir("CALL data:", data);
        // Provide your own mock by enpoint
        let mocked_handler = "mocked_" + path;
        if (!_.isUndefined(this[mocked_handler])) {
            return this[mocked_handler].call(this, data);
        }
        // Provide your own mock by service and endpoint
        mocked_handler = "mocked_" + this.usage + "_" + path;
        if (!_.isUndefined(this[mocked_handler])) {
            // Provide your own mock by enpoint and specific process
            return this[mocked_handler].call(this, data);
        }
        let result = null;
        const barcode = data
            ? data.barcode || data.identifier || data.location_barcode
            : null;
        let demo_data = this.demo_data;
        if (demo_data.by_menu_id && _.has(demo_data.by_menu_id, this.process_menu_id)) {
            // Load subset of responses by menu id
            demo_data = demo_data.by_menu_id[this.process_menu_id];
        }
        if (_.has(demo_data, barcode)) {
            // Pick a specific case for this barcode
            result = demo_data[barcode];
        }
        if (_.has(demo_data, path)) {
            // Pick general case for this path
            result = demo_data[path];
        }
        if (_.has(result, barcode)) {
            // Pick specific barcode case inside path case
            result = result[barcode];
        }
        if (_.has(result, path)) {
            // Pick the case were the 1st step is decide by the barcode
            result = result[path];
        }
        if (typeof result === "function") {
            result = result(data);
        }
        if (_.has(result, "ok")) {
            // Pick the case were you have good or bad result
            result = result.ok;
        }
        if (!result) {
            throw "NOT IMPLEMENTED: " + path;
        }
        console.dir("CALL RETURN data:", result);
        return Promise.resolve(result);
    }
    mocked_user_config(params) {
        return Promise.resolve({data: demotools.makeAppConfig()});
    }
    mocked_menu(params) {
        return Promise.resolve({data: {menus: demotools.getAppMenus()}});
    }
    mocked_scan(params) {
        const result = {};
        const data = demotools.get_indexed(params.identifier);
        if (data) {
            result.data = data;
        } else {
            result.message = {
                body: "Record not found.",
                message_type: "error",
            };
            console.log("Available index keys", Object.keys(demotools.indexed));
        }
        return Promise.resolve(result);
    }
}
