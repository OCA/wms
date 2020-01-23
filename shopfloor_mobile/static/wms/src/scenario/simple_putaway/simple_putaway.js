import {Odoo} from "../../services/odoo.js";

// TODO: init at component init
var odoo_service = new Odoo({"process_id": 1, "process_menu_id": 1})


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
            'current_state': 'scan_pack',
            'state': {
                'scan_pack': {
                    enter: () => {
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
                        this.go_state('scan_location');
                    },
                    error: (result) => {
                        this.user_notification.message = 'Operation not found';
                        this.user_notification.message_type = 'danger';
                        this.go_state('scan_pack');
                    }
                },
                'scan_location': {
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
                        this.go_state(result.state);
                    },
                    'error': (result) => {
                        this.go_state('scan_location');
                    },
                },
                'operationValided': {
                    enter: () => {
                        this.user_notification.message = 'Operation done, congrats.';
                        this.user_notification.message_type = 'success';
                        this.go_state('scan_pack');
                    }
                },
                'confirm_location': { // this one may be mered with scan_location
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
                            this.go_state('scan_location');
                        }
                    },
                    on_scan:(barcode) => {
                        this.state[this.current_state].exit();
                        this.current_state = 'scan_location';
                        this.state[this.current_state].on_scan(barcode);
                    }
                },
                'takeover': { // this one may be mered with scan_location
                    enter: () => {
                        this.user_confirmation.title = 'Destination not expected'
                        this.user_confirmation.question = 'Do you confirm the change ' + this.operation.location + '?';
                    },
                    exit: () => {},
                    on_confirmation: (answer) => {
                        if (answer == 'yes'){
                            this.go_state('scan_location');
                        } else {
                            this.go_state('scan_pack');
                        }
                    },
                    on_scan:(barcode) => {
                        this.state[this.current_state].exit();
                        this.current_state = 'scan_location';
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
                if (this.state[this.current_state].enter)
                    this.state[this.current_state].enter();
            }
        },
        scanned: function(barcode) {
            this.user_notification.message = "";
            this.state[this.current_state].on_scan(barcode);
        },
        reset: function (e) {
            console.log('on reset ');
        },
        onUserConfirmation: function(answer){
            this.state[this.current_state].on_confirmation(answer);
        },
    }
});


export function simple_putaway () { return sp }
