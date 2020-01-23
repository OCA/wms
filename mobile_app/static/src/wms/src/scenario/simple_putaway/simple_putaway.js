var odoo_service = {
    'fetchOperation': function (barcode) {
        console.log('ask odoo about barcode of pack', barcode.pack);
        return Promise.resolve({ 'source': 'def', 'destination': 'abc', 'id': 1233232, 'name': 'PACK0001', 'barcode': barcode.pack});
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
    <h1><a href="#" class="btn btn-large btn-outline-secondary" style="margin-right:10px;">&lt;</a>Simple Putaway</h1>
    {{ current_state }}
    <searchbar v-on:found="scanned" v-bind:hint="hint" v-bind:placeholder="scanTip">ici lasearch</searchbar>
    <user-information v-if="user_notification.message" v-bind:message="user_notification.message" v-bind:message_type="user_notification.message_type"></user-information>
    <user-confirmation v-if="current_state=='confirmLocation'" v-on:user-confirmation="onUserConfirmation" v-bind:title="user_confirmation.title" v-bind:question="user_confirmation.question"></user-confirmation>
    <operation-detail v-bind:operation="operation"></operation-detail>
    <form v-if="show_button" v-on:reset="reset">
        <input type="reset" name="reset"></input>
    </form>
</div>`,
    data: function () {
        return {
            'user_confirmation': {
                'title': '',
                'question': '',
            },
            'user_notification': {
                'message': '',
                'message_type': '',
            },
            'hint': 'pack',
            'show_button': false,
            'operation': {},
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
                        this.user_notification.message = 'Operation not found';
                        this.user_notification.message_type = 'danger';
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
                        this.go_state('operationSet');
                    },
                },
                'operationValided': {
                    enter: () => {
                        this.user_notification.message = 'Operation done, congrats.';
                        this.user_notification.message_type = 'success';
                        this.go_state('init');
                    }
                },
                'confirmLocation': { // this one may be mered with operationSet
                    enter: () => {
                        this.user_confirmation.title = 'Destination not expected'
                        this.user_confirmation.question = 'Do you confirm the change ' + this.operation.location + '?';
                    },
                    exit: () => {},
                    on_confirmation: (answer) => {
                        if (answer == 'yes'){
                            this.operation.confirmLocation = true;
                            this.go_state('waitOperationValidation',
                                odoo_service.validate(this.operation));
                        } else {
                            this.go_state('operationSet');
                        }
                    },
                    on_scan:(barcode) => {
                        this.state[this.current_state].exit();
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
            this.user_notification.message = "";
            this.state[this.current_state].on_scan(barcode);
        },
        reset: function (e) {
            console.log('on reest ');
            //this.reset_view();
            //odoo_service.cancel(this.operation);
        },
        onUserConfirmation: function(answer){
            this.state[this.current_state].on_confirmation(answer);
        },
    }
});


export function simple_putaway () { return sp }
