var CASE_1 = {
    'fetch' : {
        "data": {
            "id": 1,
            "location_src": {
                "id": 1,
                "name":  'Location foo baz',
            },
            "location_dst": {
                "id": 2,
                "name": 'Location bar',
            },
            "product": {"id": 1, "name": 'product name'},
            "picking": {"id": 1, "name": 'picking name'},
        },
        "state": "scan_location",
        "message": undefined
    },
    'validate' : {
        "data": undefined,
        "state": "scan_pack",
        "message": {
            'body': 'Validation OK',
            'message_type': 'info',
        }
    },
    'cancel' : {
        "data": {
            "id": 1,
            "location_src": {
                "id": 1,
                "name":  'Location foo baz',
            },
            "location_dst": {
                "id": 2,
                "name": 'Location bar',
            },
            "product": {"id": 1, "name": 'product name'},
            "picking": {"id": 1, "name": 'picking name'},
        },
        "state": "scan_location",
        "message": {"message_type": "", "title": "", "body": ""}
    }
}

var CASE_2 = {
    'fetch' : {
        "data": undefined,
        "state": "scan_pack",
        "message": {"message_type": "error", "body": "You cannot do that!"}
    },
}
var CASE_3 = {
    'fetch' : {
        "data": undefined,
        "state": "scan_pack",
        "message": {"message_type": "error", "body": "No pkg found"}
    },
}
var CASE_4 = {
    'fetch' : {
        "data": undefined,
        "state": "takeover",
        "message": {"message_type": "info", "body": "Benoit is at the toilette: do you take over?"}
    },
}
var CASE_5 = {
    'fetch' : {
        "data": {
            "id": 1,
            "location_src": {
                "id": 1,
                "name":  'Location foo baz',
            },
            "location_dst": {
                "id": 2,
                "name": 'Location Benoit',
            },
            "product": {"id": 1, "name": 'product name'},
            "picking": {"id": 1, "name": 'picking name'},
        },
        "state": "scan_location",
        "message": undefined
    },
    'cancel' : {
        "data": undefined,
        "state": "scan_pack",
        "message": undefined,
    }
}
var CASE_5 = {
    'fetch' : {
        "data": {
            "id": 1,
            "location_src": {
                "id": 1,
                "name":  'Location foo baz',
            },
            "location_dst": {
                "id": 2,
                "name": 'Location Benoit',
            },
            "product": {"id": 1, "name": 'product name'},
            "picking": {"id": 1, "name": 'picking name'},
        },
        "state": "scan_location",
        "message": undefined
    },
    'validate1' : {
        "data": undefined,
        "state": "confirm_location",
        "message": {"message_type": "warning", "body": "Are you sure of this location?"}
    },
    'validate2' : {
        "data": undefined,
        "state": "scan_pack",
        "message": undefined,
    },
}
var CASE_6 = {
    'fetch' : {
        "data": {
            "id": 1,
            "location_src": {
                "id": 1,
                "name":  'Location foo baz',
            },
            "location_dst": {
                "id": 2,
                "name": 'Location Benoit',
            },
            "product": {"id": 1, "name": 'product name'},
            "picking": {"id": 1, "name": 'picking name'},
        },
        "state": "scan_location",
        "message": undefined
    },
    'validate' : {
        "data": undefined,
        "state": "scan_location",
        "message": {"message_type": "error", "body": "You cannot move to this location"}
    },
}



var CASES = {
    "1": CASE_1,
    "2": CASE_1,
    "3": CASE_1,
    "4": CASE_1,
    "5": CASE_1,
    "6": CASE_1,
};

var CASE = CASES["1"];


export class Odoo {

    constructor(params) {
        this.params = params;
        this.process_name = this.params.process_name;
        this.process_menu = this.params.process_menu;
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
        CASE = CASES[barcode];
        // return this._call('scan_pack', 'POST', {'barcode': barcode})
        return Promise.resolve(CASE['fetch'])
    }
    validate (operation, confirmed) {
        console.log('Validate', operation);
        return Promise.resolve(CASE['validate'])
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
        return Promise.resolve(CASE['cancel'])
    }
    scanLocation (barcode) {
        return Promise.resolve(CASE['scan_loc'])
        // return this._call('scan_location', 'GET', {'barcode': barcode})
    }

}

