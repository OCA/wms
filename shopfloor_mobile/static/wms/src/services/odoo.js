export class Odoo {

    constructor(params) {
        this.params = params;
        this.process_id = this.params.process_id;
        this.process_menu_id = this.params.process_menu_id;
        // FIXME: get a real one from input
        this.api_key = '72B044F7AC780DAC'
    }

    _call(endpoint, method, data) {
        console.log('CALL', endpoint);
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
        fetch(
            this._get_url(endpoint), params
        )
        .then((response) => {
            return response.json()
        })
        .then((data) => {
            console.log('Success:', data);
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    }
    _get_headers() {
        return {
            'Content-Type': 'application/json',
            'SERVICE_CTX_MENU_ID': 1,
            'SERVICE_CTX_PROFILE_ID': 1,
            'API_KEY': this.api_key,
        }
    }

    _get_url (endpoint) {
        return '/shopfloor/' + this.process_name + '/' + endpoint;
    }
    fetchOperation (barcode) {
        console.log('Fetch', barcode);
        window.CASE = window.CASES[barcode];
        // return this._call('start', 'POST', {'barcode': barcode})
        return Promise.resolve(window.CASE['fetch'])
    }
    validate (operation, confirmed) {
        console.log('Validate', operation);
        return Promise.resolve(window.CASE['validate'])
    }
    __validate (operation, confirmed) {
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
        return Promise.resolve(window.CASE['cancel'])
    }
    scanLocation (barcode) {
        return Promise.resolve(window.CASE['scan_loc'])
        // return this._call('scan_location', 'GET', {'barcode': barcode})
    }

}

