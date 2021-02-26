/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */
import {demotools} from "../demo/demo.core.js";

export class OdooMixin {
    constructor(params) {
        this.params = params;
        this.apikey = params.apikey;
        this.usage = params.usage;
        this.headers = params.headers || {};
        this.process_menu_id = this.params.process_menu_id;
        this.profile_id = this.params.profile_id;
        this.debug = this.params.debug;
    }
    call(path, data, method = "POST", fullpath = false) {
        const endpoint = fullpath ? path : this.usage + "/" + path;
        return this._call(endpoint, method, data);
    }
    post(path, data, fullpath = false) {
        if (_.isArray(path)) {
            path = path.join("/");
        }
        const endpoint = fullpath ? path : this.usage + "/" + path;
        return this._call(endpoint, "POST", data);
    }
    get(path, data, fullpath = false) {
        if (_.isArray(path)) {
            path = path.join("/");
        }
        const endpoint = fullpath ? path : this.usage + "/" + path;
        return this._call(endpoint, "GET", data);
    }
    _call(endpoint, method, data) {
        if (this.debug) {
            console.log("CALL", endpoint);
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
        return fetch(this._get_url(endpoint), params).then(response => {
            if (!response.ok) {
                let handler = self["_handle_" + response.status.toString()];
                if (_.isUndefined(handler)) {
                    handler = this._handle_error;
                }
                return response.json().then(json => {
                    return {error: handler.call(this, response, json)};
                });
            }
            return response.json();
        });
    }
    _error_info(response, json) {
        return _.extend({}, json, {
            // strip html
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
        // /!\ IMPORTANT /!\ Always use headers w/out underscores.
        // https://www.nginx.com/resources/wiki/start/
        // topics/tutorials/config_pitfalls/#missing-disappearing-http-headers
        let headers = {
            "SERVICE-CTX-MENU-ID": this.process_menu_id,
            "SERVICE-CTX-PROFILE-ID": this.profile_id,
            "API-KEY": this.apikey,
        };
        if (method == "POST") {
            headers["Content-Type"] = "application/json";
        }
        if (!_.isEmpty(this.headers)) {
            _.merge(headers, this.headers);
        }
        return headers;
    }
    _get_url(endpoint) {
        return "/shopfloor/" + endpoint;
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
    _set_demo_data() {
        this.demo_data = demotools.get_case(this.usage);
    }
    call(path, data, method = "POST", fullpath = false) {
        this._set_demo_data();
        console.log("CALL:", path, this.usage);
        console.dir("CALL data:", data);
        if (!_.isUndefined(this[path])) {
            // Provide your own mock by enpoint
            return this[path].call(this, data);
        }
        if (!_.isUndefined(this[this.usage + "_" + path])) {
            // Provide your own mock by enpoint and specific process
            return this[this.usage + "_" + path].call(this, data);
        }
        let result;
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
        if (typeof result == "function") {
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
    user_config(params) {
        return Promise.resolve({data: demotools.makeAppConfig()});
    }
    menu(params) {
        return Promise.resolve({data: {menus: demotools.getAppMenus()}});
    }
    scan(params) {
        let result = {};
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
