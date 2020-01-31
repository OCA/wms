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
        }
    },
    methods: {
        go_state: function(state, promise) {
            console.log('GO TO STATE', state)
            this.on_exit()
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
        scanned: function(barcode) {
            this.state[this.current_state].on_scan(barcode)
        },
        on_reset: function (e) {
            this.reset_erp_data()
            this.reset_notification()
            this.go_state(this.initial_state)
        },
        onUserConfirmation: function(answer){
            this.state[this.current_state].on_confirmation(answer)
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
        }
    }
}
  