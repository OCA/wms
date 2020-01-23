import {Odoo} from "../../services/odoo.js";

// TODO: init at component init
var odoo_service = new Odoo({"process_id": 1, "process_menu_id": 1})


var sp = Vue.component('simple-pack-putaway', {
    template: `<div>
    <h1><a href="#" class="btn btn-large btn-outline-secondary" style="margin-right:10px;">&lt;</a>Simple Putaway</h1>
    {{ current_state }}
    <searchbar v-on:found="scanned" v-bind:hint="hint" v-bind:placeholder="scanTip">ici lasearch</searchbar>
    <user-information v-if="!need_confirmation && user_notification.message" v-bind:message="user_notification.message" v-bind:message_type="user_notification.message_type"></user-information>
    <user-confirmation v-if="need_confirmation" v-on:user-confirmation="onUserConfirmation" v-bind:question="user_notification.message"></user-confirmation>
    <operation-detail v-bind:operation="operation"></operation-detail>
    <form v-if="show_button" v-on:reset="reset">
        <input type="reset" name="reset"></input>
    </form>
</div>`,
    data: function () {
        return {
            'user_notification': {
                'message': '',
                'message_type': '',
            },
            'need_confirmation': false,
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
                        this.user_notification.message = false;
                        this.go_state(
                            'wait_call',
                            odoo_service.fetchOperation(scanned)
                        );
                    },
                },
                'wait_call': {
                    success: (result) => {
                        this.operation = result;
                        this.go_state(result.state);
                    }
                },
                'scan_location': {
                    enter: () => {
                        this.hint = 'location';
                        this.operation.location_barcode = null;
                    },
                    on_scan: (scanned) => {
                        this.operation.location_barcode = scanned
                        this.go_state('wait_validation',
                            odoo_service.validate(this.operation));
                    }
                },
                'wait_validation': {
                    success: (result) => {
                        this.go_state(result.state);
                    },
                    error: (result) => {
                        this.go_state('scan_location');
                    },
                },
                'confirm_location': { // this one may be mered with scan_location
                    on_confirmation: (answer) => {
                        if (answer == 'yes'){
                            this.go_state(
                                'wait_validation',
                                odoo_service.validate(this.operation, true)
                            );
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
                        this.need_confirmation = true;
                    },
                    exit: () => {
                        this.need_confirmation = false;
                    },
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
                    this.on_success,
                    this.on_error,
                );
            } else {
                if (this.state[this.current_state].enter)
                    this.state[this.current_state].enter();
            }
        },
        on_success: function (result) {
            if (result.message) {
                this.user_notification.message = result.message.body;
                this.user_notification.message_type = result.message.message_type;
                console.log('USER NOTIF', this.user_notification);
            }
            this.state[this.current_state].success(result);
        },
        on_error: function (result) {
            this.state[this.current_state].error(result);
        },
        scanned: function(barcode) {
            this.state[this.current_state].on_scan(barcode);
        },
        reset: function (e) {
            console.log('on reset ');
        },
        onUserConfirmation: function(answer){
            this.state[this.current_state].on_confirmation(answer);
            this.need_confirmation = false;
            this.user_notification.message = false;
        },
    }
});


export function simple_putaway () { return sp }
