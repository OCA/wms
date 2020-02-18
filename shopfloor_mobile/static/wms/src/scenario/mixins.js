import {Odoo, OdooMocked} from "../services/odoo.js";

export var ScenarioBaseMixin = {
    props: ['menuItem'],
    data: function () {
        return {
            'user_notification': {
                'message': '',
                'message_type': '',
            },
            'need_confirmation': false,
            'show_reset_button': false,
            'erp_data': {
                'data': {
                    // $next_state: {},
                }
            },
            'initial_state_key': 'start_scan_pack',
            'current_state_key': 'start_scan_pack',
            'states': {},
            'usage': '',  // match component usage on odoo
        }
    },
    mounted: function () {
        let odoo_params = {
            "process_id": this.menuItem.process.id,
            "process_menu_id": this.menuItem.id,
            "usage": this.usage,
        }
        if (this.$root.demo_mode)
            this.odoo = new OdooMocked(odoo_params)
        else
            // FIXME: init data should come from specific scenario
            this.odoo = new Odoo(odoo_params)
    },
    computed: {
        /*
        Full object of current state
        */
        state: function () {
            let state_data = _.result(this.erp_data.data, this.current_state_key, {})
            let state = {
                'key': this.current_state_key,
                'data': state_data,
            }
            _.extend(state, this.states[this.current_state_key])
            return state
        },
        search_input_placeholder: function () {
            return this.state.scan_placeholder
        },
        show_cancel_button: function () {
            return this.state.show_cancel_button
        }
    },
    methods: {
        state_is: function(state_key) {
            return state_key == this.current_state_key
        },
        // generic states methods
        go_state: function(state_key, promise) {
            console.log('GO TO STATE', state_key)
            if (state_key == 'start')
                // alias "start" to the initial state
                state_key = this.initial_state_key
            if (!_.has(this.states, state_key)) {
                alert('State `' + state_key + '` does not exists!')
            }
            this.on_exit()
            this.current_state_key = state_key
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
            if (this.state.enter)
                this.state.enter()
        },
        on_exit: function () {
            if (this.state.exit)
                this.state.exit()
        },
        on_success: function (result) {
            if (result.message) {
                this.set_notification(result.message)
            } else {
                this.reset_notification()
            }
            if (this.state.success)
                this.state.success(result)
        },
        on_error: function (result) {
            if (this.state.error)
                this.state.error(result)
        },
        on_reset: function (e) {
            this.reset_erp_data()
            this.reset_notification()
            this.go_state(this.initial_state_key)
        },
        // specific states methods
        on_scan: function(scanned) {
            if (this.state.on_scan)
                this.state.on_scan(scanned)
        },
        on_cancel: function() {
            if (this.state.on_cancel)
                this.state.on_cancel()
        },
        on_user_confirm: function(answer){
            this.state.on_user_confirm(answer)
            this.need_confirmation = false
            this.reset_notification()
        },
        set_notification: function(message) {
            this.user_notification.message = message.message
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
            'states': {
                // generic state for when to start w/ scanning a pack
                'start_scan_pack': {
                    enter: () => {
                        this.reset_erp_data('data')
                    },
                    on_scan: (scanned) => {
                        this.go_state(
                            'wait_call',
                            this.odoo.start(scanned.text)
                        )
                    },
                    scan_placeholder: 'Scan pack',
                },
                // generic state for when to start w/ scanning a pack or loc
                'start_scan_pack_or_location': {
                    enter: () => {
                        this.reset_erp_data('data')
                    },
                    on_scan: (scanned) => {
                        this.go_state(
                            'wait_call',
                            this.odoo.start(scanned.text)
                        )
                    },
                    scan_placeholder: 'Scan pack or location',
                },
                'wait_call': {
                    success: (result) => {
                        if (!_.isUndefined(result.data))
                            this.set_erp_data('data', result.data)
                        if (!_.isUndefined(result) && !result.error) {
                            this.go_state(result.next_state)
                        } else {
                            alert(result.status + ' ' + result.error)
                        }

                    }
                },
                'scan_location': {
                    enter: () => {
                        this.state.data.location_barcode = false
                    },
                    on_scan: (scanned) => {
                        this.state.data.location_barcode = scanned.text
                        this.go_state('wait_validation',
                            this.odoo.validate(this.state.data))
                    },
                    on_cancel: () => {
                        this.go_state('wait_cancel',
                            this.odoo.cancel(this.state.data))
                    },
                    scan_placeholder: 'Scan location',
                    show_cancel_button: true
                },
                'wait_validation': {
                    success: (result) => {
                        this.go_state(result.next_state)
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
                'confirm_location': {
                    on_user_confirm: (answer) => {
                        if (answer == 'yes'){
                            this.go_state(
                                'wait_call',
                                this.odoo.confirm_start(this.state.data, true)
                            )
                        } else {
                            this.go_state('scan_location')
                        }
                    },
                    on_scan: (scanned) => {
                        this.on_exit()
                        this.current_state_key = 'scan_location'
                        this.state.on_scan(scanned)
                    }
                },
                'confirm_start': {
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
                            this.go_state('start')
                        }
                    },
                    on_scan:(scanned) => {
                        this.on_exit()
                        this.current_state_key = 'scan_location'
                        this.state.on_scan(scanned)
                    }
                },
            }
        }
    }
}
