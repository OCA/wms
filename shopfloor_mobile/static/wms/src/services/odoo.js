import {Storage} from './storage.js'


export class OdooMixin {

    constructor(params) {
        this.params = params;
        this.usage = params.usage
        this.process_id = this.params.process_id
        this.process_menu_id = this.params.process_menu_id
        this.debug = this.params.debug
    }
    call(path, data, method='POST', fullpath=false) {
        let endpoint = fullpath ? path : this.usage + '/' + path
        return this._call(endpoint, data, method)
    }
    _call(endpoint, method, data) {
        if (this.debug) console.log('CALL', endpoint)
        let self = this;
        let params = {
            method: method,
            headers: this._get_headers()
        }
        if (data !== undefined) {
            if (method == 'GET') {
                endpoint += '?' + new URLSearchParams(data).toString();
            } else if (method == 'POST') {
                params['body'] = JSON.stringify(data);
            }
        }
        return fetch(
            this._get_url(endpoint), params
        )
        .then((response) => {
            if (response.ok) {
                return response.json()
            }
            else {
                let handler = self['_handle_' + response.status.toString()]
                if (_.isUndefined(handler))
                    handler = this._handle_error
                return handler.call(this, response);
            }
        });
    }
    _error_info (response) {
        return {
            'error': response.statusText,
            'status': response.status,
            'response': response,
        }
    }
    _handle_403(response) {
        Storage.apikey = "";
        return this._error_info(response)
    }
    _handle_404(response) {
        console.log('Endpoint not found, please check your odoo configuration. URL: ', response.url)
        return this._error_info(response)
    }
    _handle_500(response) {
        return this._error_info(response)
    }
    _handle_error(response) {
        console.log(response.status, response.statusText, response.url)
        return this._error_info(response)
    }
    _get_headers() {
        return {
            'Content-Type': 'application/json',
            'SERVICE_CTX_MENU_ID': this.process_menu_id,
            'SERVICE_CTX_PROFILE_ID': 1, // FIXME
            'API_KEY': Storage.apikey,
        }
    }
    _get_url (endpoint) {
        return '/shopfloor/' + endpoint
    }
}


export class OdooMocked extends OdooMixin{

    start (data) {
        window.DEMO_CASE = window.DEMO_CASES[this.usage][data.barcode]
        return Promise.resolve(window.DEMO_CASE['start'])
    }
    scan_anything (barcode) {
        console.log('Scan anything', barcode, this.usage);
        window.DEMO_CASE = window.DEMO_CASES[this.usage][barcode]
        if (!window.DEMO_CASE) {
            return Promise.resolve({
                "message": {"message_type": "error", "message": "Unknown barcode"}
            })
        }
        let res = window.DEMO_CASE['fetch'];
        // console.log(res);
        return Promise.resolve(res)
    }
    call(path, data, method='POST', fullpath=false) {
        console.log('CALL:', path, this.usage);
        if (!_.isUndefined(this[path])) {
            // provide your own mock by enpoint
            return this[path].call(this, data)
        }
        if (!_.isUndefined(this[this.usage + '_' + path])) {
            // provide your own mock by enpoint and specific process
            return this[this.usage + '_' + path].call(this, data)
        }
        if (_.isEmpty(window.DEMO_CASE))
            // no demo case picked yet, find by process
            window.DEMO_CASE = window.DEMO_CASES[this.usage]
        let result
        let barcode = data.barcode || data.location_barcode
        if (_.has(window.DEMO_CASE, barcode)) {
            // pick a specific case for this barcode
            result = window.DEMO_CASE[barcode]
        }
        if (_.has(window.DEMO_CASE, path)) {
            // pick general case for this path
            result = window.DEMO_CASE[path]
        }
        if (_.has(result, barcode)) {
            // pick specific barcode case inside path case
            result = result[barcode]
        }
        if (_.has(result, 'ok')) {
            // pick the case were you have good or bad result
            result = result['ok']
        }
        if (!result) {
            throw 'NOT IMPLEMENTED: ' + path
        }
        return Promise.resolve(result)
    }
}


export class Odoo extends OdooMixin{

    // TODO: review and drop very specific methods, move calls to specific components
    start (barcode) {
        return this.call('start', 'POST', {'barcode': barcode})
    }
    scan_anything (barcode) {
        console.log('Scan anything', barcode, this.usage);
        throw 'NOT IMPLEMENTED!'
    }

}
