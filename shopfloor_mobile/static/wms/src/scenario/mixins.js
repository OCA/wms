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
    beforeMount: function () {
        if (this.$root.demo_mode) {
            this.$root.loadJS('src/demo/demo.' + this.usage + '.js', this.usage)
        }
    },
    mounted: function () {
        let odoo_params = {
            "process_id": this.menuItem.process.id,
            "process_menu_id": this.menuItem.id,
            "usage": this.usage,
            "debug": this.$root.demo_mode
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
            let state = {
                'key': this.current_state_key,
                'data': this._state_get_data_raw(this.current_state_key),
            }
            _.extend(state, this.states[this.current_state_key])
            _.defaults(state, {'display_info': {}})
            return state
        },
        search_input_placeholder: function () {
            if (this.state.scan_placeholder) {
                // TMP backward compat
                return this.state.scan_placeholder
            }
            return this.state.display_info.scan_placeholder
        },
        show_cancel_button: function () {
            return this.state.display_info.show_cancel_button
        }
    },
    methods: {
        state_is: function(state_key) {
            return state_key == this.current_state_key
        },
        state_in: function(state_keys) {
            return _.filter(state_keys, this.state_is).length > 0;
        },
        _state_get_data_raw: function(state_key) {
            return _.result(this.erp_data.data, state_key, {})
        },
        state_get_data: function(state_key) {
            state_key = _.isUndefined(state_key) ? this.current_state_key : state_key
            return this._state_get_data_raw(state_key)
        },
        state_set_data: function(data, state_key) {
            state_key = _.isUndefined(state_key) ? this.current_state_key : state_key
            let new_data = _.merge(this._state_get_data_raw(state_key), data)
            this.$set(this.erp_data.data, state_key, new_data)
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
            this.on_enter()
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
        },
        reset_notification: function() {
            this.user_notification.message = false
            this.user_notification.message_type = false
        },
        set_erp_data: function (key, data) {
            let new_data = this.erp_data[key]
            _.merge(new_data, data)
            this.$set(this.erp_data, key, new_data)
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
                    display_info: {
                        'title': 'Start by scanning a pack',
                        'scan_placeholder': 'Scan pack',
                    },
                    enter: () => {
                        this.reset_erp_data('data')
                    },
                    on_scan: (scanned) => {
                        this.go_state(
                            'wait_call',
                            this.odoo.call('start', {'barcode': scanned.text})
                        )
                    },
                },
                // generic state for when to start w/ scanning a pack or loc
                'start_scan_pack_or_location': {
                    display_info: {
                        'title': 'Start by scanning a pack or a location',
                        'scan_placeholder': 'Scan pack',
                    },
                    enter: () => {
                        this.reset_erp_data('data')
                    },
                    on_scan: (scanned) => {
                        this.go_state(
                            'wait_call',
                            this.odoo.call('start', {'barcode': scanned.text})
                        )
                    },
                },
                'wait_call': {
                    success: (result) => {
                        if (!_.isUndefined(result.data))
                            this.set_erp_data('data', result.data)
                        if (!_.isUndefined(result) && !result.error) {
                            // TODO: consider not changing the state if it is the same to no refresh
                            this.go_state(result.next_state)
                        } else {
                            alert(result.status + ' ' + result.error)
                        }

                    }
                },
                // TODO: these states should be splitted out to a specific mixin
                // for putaway and pack transfer
                'scan_location': {
                    display_info: {
                        'title': 'Set a location',
                        'scan_placeholder': 'Scan location',
                        'show_cancel_button': true,
                    },
                    on_scan: (scanned, confirmation=false) => {
                        this.state_set_data({'location_barcode': scanned.text})
                        this.go_state('wait_validation',
                            this.odoo.call('validate', {
                                'package_level_id': this.state.data.id,
                                'location_barcode': scanned.text,
                                'confirmation': confirmation,
                            })
                        )
                    },
                    on_cancel: () => {
                        this.go_state('wait_cancel',
                            this.odoo.call('cancel', {
                                'package_level_id': this.state.data.id,
                            })
                        )
                    },
                },
                'wait_validation': {
                    success: (result) => {
                        if (!_.isUndefined(result.data)){
                            this.set_erp_data('data', result.data)
                        }
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
                    display_info: {
                        'scan_placeholder': 'Scan location',
                    },
                    enter: () => {
                        this.need_confirmation = true
                    },
                    exit: () => {
                        this.need_confirmation = false
                    },
                    on_user_confirm: (answer) => {
                        if (answer == 'yes'){
                            // Reuse data from scan_location and
                            // simulate the event that on_scan expects
                            let scan_data = this.state_get_data('scan_location')
                            this.state.on_scan({
                                'text': scan_data.location_barcode
                            }, true)
                        } else {
                            this.go_state('scan_location')
                        }
                    },
                    on_scan: (scanned, confirmation=true) => {
                        this.on_exit()
                        this.current_state_key = 'scan_location'
                        this.state.on_scan(scanned, confirmation)
                    },
                },
                'confirm_start': {
                    display_info: {
                        'title': 'Confirm start and select a location',
                        'scan_placeholder': 'Scan location',
                    },
                    enter: () => {
                        this.need_confirmation = true
                    },
                    exit: () => {
                        this.need_confirmation = false
                    },
                    on_user_confirm: (answer) => {
                        if (answer == 'yes'){
                            // Keep the data received from previous state but not the question answered
                            let state_data = this.state_get_data(this.current_state_key)
                            state_data.message = {}
                            this.state_set_data(state_data, 'scan_location')
                            this.go_state('scan_location')
                        } else {
                            this.go_state('start')
                        }
                    },
                    on_scan:(scanned) => {
                        this.on_exit()
                        this.current_state_key = 'scan_location'
                        this.state.on_scan(scanned)
                    },
                },
            }
        }
    }
}
