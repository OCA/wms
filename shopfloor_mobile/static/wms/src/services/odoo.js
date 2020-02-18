import {Storage} from './storage.js'


export class OdooMixin {

    constructor(params) {
        this.params = params;
        this.usage = params.usage;
        this.process_id = this.params.process_id;
        this.process_menu_id = this.params.process_menu_id;
    }

    _call(endpoint, method, data) {
        console.log('CALL', endpoint);
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

    start (barcode) {
        console.log('Fetch', barcode);
        window.DEMO_CASE = window.DEMO_CASES[this.usage][barcode];
        let res = window.DEMO_CASE['fetch'];
        console.log(res);
        return Promise.resolve(res)
        // return this._call('start', 'POST', {'barcode': barcode})
    }
    validate (operation, confirmed) {
        console.log('Validate', operation);
        let res = window.DEMO_CASE['validate'];
        if (operation.location_barcode in window.DEMO_CASE)
            res = window.DEMO_CASE[operation.location_barcode]
        console.log(res);
        return Promise.resolve(res)
    }
    cancel(id) {
        console.log('Cancelling', id);
        let res = window.DEMO_CASE['cancel'];
        console.log(res);
        return Promise.resolve(res)
    }
    scan_location (barcode) {
        if (_.isEmpty(window.DEMO_CASE))
            window.DEMO_CASE = window.DEMO_CASES[this.usage][barcode]
        return Promise.resolve(window.DEMO_CASE['scan_loc'])
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
    // picking_load_trip
    find_batch () {
        console.log('find_batch', this.usage);
        if (_.isEmpty(window.DEMO_CASE))
            window.DEMO_CASE = window.DEMO_CASES[this.usage]
        return Promise.resolve(window.DEMO_CASE['find_batch'])
    }
    picking_batch () {
        console.log('picking_batch', this.usage);
        throw '.picking_batch NOT IMPLEMENTED!'
    }
    confirm_start () {
        console.log('confirm_start', this.usage);
        return Promise.resolve(window.DEMO_CASE['confirm_start'])
    }
    unassign () {
        console.log('unassign', this.usage);
        return Promise.resolve(window.DEMO_CASE['unassign'])
    }
    scan_line () {
        console.log('scan_line', this.usage);
        return Promise.resolve(window.DEMO_CASE['scan_line'])
    }
    scan_destination_pack () {
        console.log('scan_destination_pack', this.usage);
        return Promise.resolve(window.DEMO_CASE['scan_destination_pack'])
    }
    prepare_unload () {
        console.log('prepare_unload', this.usage);
        throw '.prepare_unload NOT IMPLEMENTED!'
    }
    select () {
        console.log('select', this.usage);
        throw '.select NOT IMPLEMENTED!'
    }

}


export class Odoo extends OdooMixin{

    start (barcode) {
        return this._call(this.usage + '/start', 'POST', {'barcode': barcode})
    }
    validate (operation, confirmed) {
        console.log('Validate', operation);
        let data = {
            'package_level_id': operation.id, 'location_barcode': operation.location_barcode
        }
        if (!_.isUndefined(confirmed))
            data['confirmation'] = true;
        return this._call(this.usage + '/validate', 'POST', data)
    }
    cancel(id) {
        console.log('Cancelling', id);
        return this._call(this.usage + '/cancel', 'POST', {'barcode': barcode})
    }
    scan_location (barcode) {
        return this._call(this.usage + '/scan_location', 'POST', {'barcode': barcode})
    }
    scan_anything (barcode) {
        console.log('Scan anything', barcode, this.usage);
        throw 'NOT IMPLEMENTED!'
    }
    // picking_load_trip
    find_batch () {
        throw '.find_batch NOT IMPLEMENTED!'
    }
    picking_batch () {
        throw '.picking_batch NOT IMPLEMENTED!'
    }
    unassign () {
        throw '.unassign NOT IMPLEMENTED!'
    }
    scan_line () {
        throw '.scan_line NOT IMPLEMENTED!'
    }
    scan_destination_pack () {
        throw '.scan_destination_pack NOT IMPLEMENTED!'
    }
    prepare_unload () {
        throw '.prepare_unload NOT IMPLEMENTED!'
    }
    select () {
        throw '.select NOT IMPLEMENTED!'
    }

}
