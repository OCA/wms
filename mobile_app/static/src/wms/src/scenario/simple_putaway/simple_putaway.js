var odoo_service = {
    'fetchOperation': function (barcode) {
        console.log('ask odoo about barcode of pack', barcode.pack);
        return Promise.resolve({ 'source': 'def', 'destination': 'abc', 'id': 1233232, 'name': 'PACK0001'});
    },
    'scanLocation': function (barcode) {
        if (barcode.indexOf('a') != -1) {
            return Promise.resolve(barcode);
        } else {
            return Promise.reject('Invalid Location');
        } 
    },
    'cancel': function (operation) {
        console.log('tell odoo to cancel the move', operation.id);
    },
    'validate': function(operation) {
        console.log('Validate the move ', operation.id, ' on location dest: ', operation.location_suggested);
        if (operation.confirmLocation) {
            console.log('the guy confirmed, we accept then')
            return Promise.resolve({ pleaseConfirm: false});
        }
        if (operation.location_suggested == operation.destination) {
            return Promise.resolve({ pleaseConfirm: false});
        } else {
            return Promise.resolve({ pleaseConfirm: true});
        }
    },
}


var sp = Vue.component('simple-pack-putaway', {
    template: `<div>
    <h1>Simple Putaway</h1>
    {{ current_state }}
    <searchbar v-on:found="scanned" v-bind:hint="hint" v-bind:placeholder="scanTip">ici lasearch</searchbar>
    <div class="alert alert-danger error" v-if="error_msg" role="alert">{{ error_msg }}</div>
    <operation-detail v-bind:operation="operation"></operation-detail>
    <div v-if="show_confirm" class="confirm">
        <div class="alert alert-danger error" v-if="error_msg" role="alert">
            <h4 class="alert-heading">Destination not expected</h4>
            <p>Do you confirm? {{ confirm_with }} </p>
            <form v-on:submit="doConfirm" v-on:reset="dontConfirm">
               <input class="btn btn-lg btn-success" type="submit" value="Yes"></input>
               <input class="btn btn-lg btn-danger float-right" type="reset" value="No"></input>
            </form>
    </div>
    <form v-if="show_button" v-on:reset="reset">
        <input type="reset" name="reset"></input>
    </form>
</div>`,
    data: function () {
        return {
            'hint': 'pack',
            'show_button': false,
            'operation': {},
            'error_msg': '',
            'show_confirm': false,
            'current_state': 'init',
            'state': {
                'init': {
                    enter: () => {
                        this.reset();
                        this.hint = 'pack';
                    },
                    on_scan: (scanned) => {
                        this.go_state(
                            'waitFetchOperation',
                            odoo_service.fetchOperation({
                                'pack': scanned
                            })
                        );
                    },
                },
                'waitFetchOperation': {
                    success: (result) => {
                        this.operation = result;
                        this.go_state('operationSet');
                    },
                    'error': (result) => {
                        console.error('no operation found');
                        this.go_state('init');
                    }
                },
                'operationSet': {
                    enter: () => {
                        this.hint = 'location';
                        this.operation.location_suggested = null;
                    },
                    on_scan: (scanned) => {
                        this.operation.location_suggested = scanned
                        this.go_state('waitOperationValidation',
                            odoo_service.validate(this.operation));
                    }
                },
                'waitOperationValidation': {
                    'success': (result) => {
                        if (result.pleaseConfirm) {
                            this.go_state('confirmLocation');
                        } else {
                            this.go_state('operationValided');
                        }
                    },
                    'error': (result) => {
                        'operationSet'
                    },
                },
                'operationValided': {
                    enter: () => {
                        console.log('display congratulation');
                        this.go_state('init');
                    }
                }, // = done
                'confirmLocation': { // this one may be mered with operationSet
                    enter: () => {
                        this.show_confirm = true;
                    },
                    exit: () => {
                        console.log('exit');
                        this.show_confirm = false;
                    },
                    'doConfirm': () => { //confirm location
                        // tell the server we are sure
                        this.operation.confirmLocation = true;
                        this.go_state('waitOperationValidation',
                            odoo_service.validate(this.operation));
                    },
                    'dontConfirm': () => {
                        this.go_state('operationSet');
                    },
                    on_scan:(barcode) => {
                        this.current_state = 'operationSet';
                        this.state[this.current_state].on_scan(barcode);
                    }
                },
            }
        };
    },
    computed: {
      scanTip: function () {
        return this.hint == 'pack' ? 'Scan pack': 'Scan location'
      }
    },
    methods: {
        go_state: function(state, promise) {
            if (this.state[this.current_state].exit)
                this.state[this.current_state].exit();
            this.current_state = state;
            if (promise) {
                promise.then(
                    this.state[state].success,
                    this.state[state].error,
                );
            } else {
                this.state[state].enter();
            }
        },
        scanned: function(barcode) {
            this.state[this.current_state].on_scan(barcode);
        },
        doConfirm: function (e) {
            e.preventDefault();
            this.state[this.current_state].doConfirm();
        },
        dontConfirm: function (e) {
            e.preventDefault();
            this.state[this.current_state].dontConfirm();
        },
        reset: function (e) {
            console.log('on reest ');
            this.reset_view();
            odoo_service.cancel(this.operation);
        },
    }
});


export function simple_putaway () { return sp }
