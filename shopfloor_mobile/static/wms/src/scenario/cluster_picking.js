import {ScenarioBaseMixin, GenericStatesMixin} from "./mixins.js";

/*
<searchbar v-if="current_state_key == initial_state_key" v-on:found="on_scan" :input_placeholder="search_input_placeholder"></searchbar>
<searchbar v-if="current_state_key == 'scan_location'" v-on:found="on_scan" :input_placeholder="search_input_placeholder" :input_data_type="'location'"></searchbar>
<user-information v-if="!need_confirmation && user_notification.message" v-bind:info="user_notification"></user-information>
<user-confirmation v-if="need_confirmation" v-on:user-confirmation="on_user_confirm" v-bind:question="user_notification.message"></user-confirmation>
<operation-detail :operation="state.data"></operation-detail>
<last-operation v-if="current_state_key == 'show_completion_info'" v-on:confirm="state['show_completion_info'].on_confirm"></last-operation>
<cancel-button v-on:cancel="on_cancel" v-if="show_cancel_button"></cancel-button>
*/

export var ClusterPicking = Vue.component('cluster-picking', {
    mixins: [ScenarioBaseMixin, GenericStatesMixin],
    template: `
        <Screen title="Single pack transfer">
            <!-- FOR DEBUG -->
            <!-- {{ current_state_key }} -->
            <get-work v-if="is_state(initial_state_key)"
                      v-on:get_work="state.on_get_work"
                      v-on:manual_selection="state.on_manual_selection"></get-work>
            <div class="work-info">
            </div>
        </Screen>
    `,
    data: function () {
        return {
            'usage': 'picking_loading_trip',
            'show_reset_button': true,
            'initial_state_key': 'start',
            'current_state_key': 'start',
            'states': {
                'start': {
                    enter: () => {
                        this.reset_erp_data('data')
                    },
                    on_get_work: (evt) => {
                        this.go_state(
                            'wait_call',
                            this.odoo.find_batch()
                        )
                    },
                    on_manual_selection: (evt) => {
                        this.go_state(
                            'wait_call',
                            this.odoo.picking_batch()
                        )
                    },
                },
                'start_manual_selection': {
                    enter: () => {
                        this.reset_erp_data('data')
                    },
                    on_submit_back: () => {
                        this.go_state('start')
                    },
                    on_select: (selected) => {
                        this.go_state(
                            'wait_call',
                            this.odoo.select(selected)
                        )
                    },
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
                            this.go_state(
                                'wait_call',
                                this.odoo.confirm_start(this.state.data)
                            )
                        } else {
                            this.go_state(
                                'wait_call',
                                this.odoo.unassign(this.state.data)
                            )
                        }
                    },
                },
                'start_line': {
                    // here we have to use some info sent back from `select`
                    // or from `find_batch` that we pass to scan line
                    on_scan: (scanned) => {
                        this.go_state(
                            'wait_call',
                            this.odoo.scan_line(this.state.data.move_id, scanned.text)
                        )
                    },
                    on_full_bin: () => {
                        this.go_state(
                            'wait_call',
                            this.odoo.prepare_unload(scanned.text)
                        )
                    },
                    scan_placeholder: 'Scan location / pack / product / lot',
                },
                'scan_destination': {
                    on_scan: (scanned) => {
                        this.go_state(
                            'wait_call',
                            this.odoo.scan_line(this.state.data.move_id, scanned.text)
                        )
                    },
                    on_button_action: () => {
                        this.go_state(
                            'wait_call',
                            this.odoo.prepare_unload(scanned.text)
                        )
                    },
                    scan_placeholder: 'Scan location / pack / product / lot',
                },
                'show_completion_info': {
                    on_confirm: () => {
                        // TODO: turn the cone?
                        this.go_state('start')
                    },
                },
            }
        }
    },
})
