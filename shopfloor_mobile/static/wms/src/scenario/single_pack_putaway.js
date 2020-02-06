import {ScenarioBaseMixin} from "../mixins.js";

Vue.component('single-pack-putaway', {
    mixins: [ScenarioBaseMixin],
    template: `
        <Screen title="Single pack putaway">
            <!-- FOR DEBUG -->
            <!-- {{ current_state }} -->
            <searchbar v-on:found="scanned" :input_placeholder="search_input_placeholder"></searchbar>
            <user-information v-if="!need_confirmation && user_notification.message" v-bind:info="user_notification"></user-information>
            <user-confirmation v-if="need_confirmation" v-on:user-confirmation="onUserConfirmation" v-bind:question="user_notification.message"></user-confirmation>
            <operation-detail :operation="erp_data.data"></operation-detail>
            <reset-screen-button v-on:reset="on_reset" :show_reset_button="show_reset_button"></reset-screen-button>
        </Screen>
    `,
    data: function () {
        return {
            'usage': 'single_pack_putaway',
            'show_reset_button': true,
            'initial_state': 'scan_pack',
            'current_state': 'scan_pack',
            'state': {
                'scan_pack': {
                    enter: () => {
                        this.reset_erp_data('data')
                    },
                    on_scan: (scanned) => {
                        this.go_state(
                            'wait_call',
                            this.odoo.scan_pack(scanned)
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
                        this.erp_data.data.location_barcode = scanned
                        this.go_state('wait_validation',
                            this.odoo.validate(this.erp_data.data))
                    },
                    scan_placeholder: 'Scan location',
                },
                'wait_validation': {
                    success: (result) => {
                        this.go_state(result.state)
                    },
                    error: (result) => {
                        this.go_state('scan_location')
                    },
                },
                'confirm_location': { // this one may be mered with scan_location
                    on_confirmation: (answer) => {
                        if (answer == 'yes'){
                            this.go_state(
                                'wait_validation',
                                this.odoo.validate(this.erp_data.data, true)
                            )
                        } else {
                            this.go_state('scan_location')
                        }
                    },
                    on_scan:(barcode) => {
                        this.on_exit()
                        this.current_state = 'scan_location'
                        this.state[this.current_state].on_scan(barcode)
                    }
                },
                'takeover': { // this one may be mered with scan_location
                    enter: () => {
                        this.need_confirmation = true
                    },
                    exit: () => {
                        this.need_confirmation = false
                    },
                    on_confirmation: (answer) => {
                        if (answer == 'yes'){
                            this.go_state('scan_location')
                        } else {
                            this.go_state('scan_pack')
                        }
                    },
                    on_scan:(barcode) => {
                        this.on_exit()
                        this.current_state = 'scan_location'
                        this.state[this.current_state].on_scan(barcode)
                    }
                },
            }
        }
    },
})
