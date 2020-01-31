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
                if (handler !== undefined) {
                    handler(response);
                } else {
                    console.log(response.statusText)
                }
            }
        });
    }
    _handle_403(response) {
        Storage.apikey = "";
        throw "Invalid API KEY";
    }
    _handle_404(response) {
        throw `Endpoint not found, please check your odoo configuration.
        URL: ` + response.url
    }
    _get_headers() {
        console.log('APIKEY', Storage.apikey)
        return {
            'Content-Type': 'application/json',
            'SERVICE_CTX_MENU_ID': 1,
            'SERVICE_CTX_PROFILE_ID': 1,
            'API_KEY': Storage.apikey,
        }
    }
    _get_url (endpoint) {
        return '/shopfloor/' + this.usage + '/' + endpoint;
    }
}


export class OdooMocked extends OdooMixin{
    
    scan_pack (barcode) {
        console.log('Fetch', barcode);
        window.CASE = window.CASES[barcode];
        let res = window.CASE['fetch'];
        console.log(res);
        return Promise.resolve(res)
        // return this._call('start', 'POST', {'barcode': barcode})
    }
    validate (operation, confirmed) {
        console.log('Validate', operation);
        let res = window.CASE['validate'];
        if (operation.location_barcode in window.CASE)
            res = window.CASE[operation.location_barcode]
        console.log(res);
        return Promise.resolve(res)
    }
    cancel(id) {
        console.log('Cancelling', id);
        let res = window.CASE['cancel'];
        console.log(res);
        return Promise.resolve(res)
    }
    scan_location (barcode) {
        return Promise.resolve(window.CASE['scan_loc'])
    }

}


export class Odoo extends OdooMixin{
    
    scan_pack (barcode) {
        return this._call('scan_pack', 'POST', {'barcode': barcode})
    }
    validate (operation, confirmed) {
        console.log('Validate', operation);
        let data = {
            'id': operation.id, 'location_barcode': operation.location_barcode
        }
        if (confirmed !== undefined)
            data['confirmed'] = true;
        return this._call('validate', 'POST', data)
    }
    cancel(id) {
        console.log('Cancelling', id);
        return this._call('cancel', 'POST', {'barcode': barcode})
    }
    scan_location (barcode) {
        return this._call('scan_location', 'POST', {'barcode': barcode})
    }

}

