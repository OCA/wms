import {ScenarioBaseMixin, GenericStatesMixin} from "./mixins.js";

export var ClusterPicking = Vue.component('cluster-picking', {
    mixins: [ScenarioBaseMixin, GenericStatesMixin],
    template: `
        <Screen :title="menuItem.name">
            <!-- FOR DEBUG -->
            <!-- {{ current_state_key }} -->
            <get-work
                v-if="is_state(initial_state_key)"
                v-on:get_work="state.on_get_work"
                v-on:manual_selection="state.on_manual_selection"></get-work>
            <batch-picking-detail
                v-if="is_state('confirm_start')"
                :info="state.data"
                v-on:confirm="state.on_confirm"
                v-on:cancel="state.on_cancel"
                ></batch-picking-detail>
        </Screen>
    `,
    data: function () {
        return {
            'usage': 'cluster_picking',
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
                    on_confirm: () => {
                        this.go_state(
                            'wait_call',
                            this.odoo.confirm_start(this.state.data)
                        )
                    },
                    on_cancel: () => {
                        this.go_state(
                            'wait_call',
                            this.odoo.unassign(this.state.data)
                        )
                    } 
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
