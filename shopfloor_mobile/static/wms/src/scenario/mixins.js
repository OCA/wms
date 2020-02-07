import {Odoo, OdooMocked} from "../services/odoo.js";

export var ScenarioBaseMixin = {
    data: function () {
        return {
            'user_notification': {
                'message': '',
                'message_type': '',
            },
            'need_confirmation': false,
            'show_reset_button': false,
            'erp_data': {
                'data': {}
            },
            'initial_state': 'scan_pack',
            'current_state': 'scan_pack',
            'state': {},
            'usage': '',  // match component usage on odoo
        }
    },
    mounted: function () {
        if (this.$root.demo_mode)
            this.odoo = new OdooMocked({
                "process_id": 1, "process_menu_id": 1, "usage": this.usage,
            })
        else
            // FIXME: init data should come from specific scenario
            this.odoo = new Odoo({
                "process_id": 1, "process_menu_id": 1, "usage": this.usage,
            })
    },
    computed: {
        search_input_placeholder: function () {
            return this.state[this.current_state].scan_placeholder
        },
        show_cancel_button: function () {
            return this.state[this.current_state].show_cancel_button
        }
    },
    methods: {
        // generic states methods
        go_state: function(state, promise) {
            console.log('GO TO STATE', state)
            this.on_exit()
            if (state == 'start')
                // alias "start" to the initial state
                state = this.initial_state
            this.current_state = state
            if (promise) {
                promise.then(
                    this.on_success,
                    this.on_error,
                )
            } else {
                this.on_enter()
            }
        },
        on_enter: function () {
            if (this.state[this.current_state].enter)
                this.state[this.current_state].enter()
        },
        on_exit: function () {
            if (this.state[this.current_state].exit)
                this.state[this.current_state].exit()
        },
        on_success: function (result) {
            if (result.message) {
                this.set_notification(result.message)
            } else {
                this.reset_notification()
            }
            if (this.state[this.current_state].success)
                this.state[this.current_state].success(result)
        },
        on_error: function (result) {
            if (this.state[this.current_state].error)
                this.state[this.current_state].error(result)
        },
        on_reset: function (e) {
            this.reset_erp_data()
            this.reset_notification()
            this.go_state(this.initial_state)
        },
        // specific states methods
        on_scan: function(scanned) {
            if (this.state[this.current_state].on_scan)
                this.state[this.current_state].on_scan(scanned)
        },
        on_cancel: function() {
            if (this.state[this.current_state].on_cancel)
                this.state[this.current_state].on_cancel()
        },
        on_user_confirm: function(answer){
            this.state[this.current_state].on_user_confirm(answer)
            this.need_confirmation = false
            this.reset_notification()
        },
        set_notification: function(message) {
            this.user_notification.message = message.body
            this.user_notification.message_type = message.message_type
            console.log('USER NOTIF SET', this.user_notification)
        },
        reset_notification: function() {
            this.user_notification.message = false
            this.user_notification.message_type = false
            console.log('USER NOTIF RESET')
        },
        set_erp_data: function (key, data) {
            this.$set(this.erp_data, key, data)
        },
        reset_erp_data: function (key) {
            // FIXME
            this.$set(this.erp_data, key, {})
        },
    }
}


export var GenericStatesMixin = {

    data: function () {
        return {
            'state': {
                'scan_pack': {
                    enter: () => {
                        this.reset_erp_data('data')
                    },
                    on_scan: (scanned) => {
                        this.go_state(
                            'wait_call',
                            this.odoo.scan_pack(scanned.text)
                        )
                    },
                    scan_placeholder: 'Scan pack',
                },
                'wait_call': {
                    success: (result) => {
                        if (result.data != undefined)
                            this.set_erp_data('data', result.data)
                        this.go_state(result.state)
                    }
                },
                'scan_location': {
                    enter: () => {
                        this.erp_data.data.location_barcode = false
                    },
                    on_scan: (scanned) => {
                        this.erp_data.data.location_barcode = scanned.text
                        this.go_state('wait_validation',
                            this.odoo.validate(this.erp_data.data))
                    },
                    on_cancel: () => {
                        this.go_state('wait_cancel',
                            this.odoo.cancel(this.erp_data.data))
                    },
                    scan_placeholder: 'Scan location',
                    show_cancel_button: true
                },
                'wait_validation': {
                    success: (result) => {
                        this.go_state(result.state)
                    },
                    error: (result) => {
                        this.go_state('scan_location')
                    },
                },
                'wait_cancel': {
                    success: (result) => {
                        this.go_state('start')
                    },
                    error: (result) => {
                        this.go_state('start')
                    },
                },
                'confirm_location': { // this one may be mered with scan_location
                    on_user_confirm: (answer) => {
                        if (answer == 'yes'){
                            this.go_state(
                                'wait_validation',
                                this.odoo.validate(this.erp_data.data, true)
                            )
                        } else {
                            this.go_state('scan_location')
                        }
                    },
                    on_scan: (scanned) => {
                        this.on_exit()
                        this.current_state = 'scan_location'
                        this.state[this.current_state].on_scan(scanned)
                    }
                },
                'takeover': { // this one may be mered with scan_location
                    enter: () => {
                        this.need_confirmation = true
                    },
                    exit: () => {
                        this.need_confirmation = false
                    },
                    on_user_confirm: (answer) => {
                        if (answer == 'yes'){
                            this.go_state('scan_location')
                        } else {
                            this.go_state('scan_pack')
                        }
                    },
                    on_scan:(scanned) => {
                        this.on_exit()
                        this.current_state = 'scan_location'
                        this.state[this.current_state].on_scan(scanned)
                    }
                },
            }
        }
    }
}