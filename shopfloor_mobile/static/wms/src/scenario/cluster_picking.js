import {ScenarioBaseMixin, GenericStatesMixin} from "./mixins.js";

export var ClusterPicking = Vue.component('cluster-picking', {
    mixins: [ScenarioBaseMixin, GenericStatesMixin],
    template: `
        <Screen :title="menuItem.name" :klass="usage">
            <!-- FOR DEBUG -->
            <!-- {{ current_state_key }} -->
            <template v-slot:header v-if="state.display_info">
                <state-display-info :info="state.display_info" />
            </template>
            <!-- TODO: move it above everything -->
            <user-information
                v-if="!need_confirmation && user_notification.message"
                v-bind:info="user_notification"
                />
            <searchbar
                v-if="state_in(['start_line', 'unload_all', 'confirm_unload_all', 'scan_destination'])"
                v-on:found="on_scan"
                :input_placeholder="search_input_placeholder"
                />
            <get-work
                v-if="state_is(initial_state_key)"
                v-on:get_work="state.on_get_work"
                v-on:manual_selection="state.on_manual_selection"
                />
            <batch-picking-detail
                v-if="state_is('confirm_start')"
                :info="state.data"
                v-on:confirm="state.on_confirm"
                v-on:cancel="state.on_cancel"
                />
            <batch-picking-line-detail
                v-if="state_in(['start_line', 'scan_destination'])"
                :line="state.data"
                :show-full-info="!state_is('scan_destination')"
                />
            <batch-picking-line-actions
                v-if="state_is('start_line')"
                v-on:action="state.on_action"
                :line="state_get_data('start_line')"
                />
            <div v-if="state_is('scan_destination')">
                <div class="qty">
                    <input-number-spinner v-on:input="state.on_qty_update" :init_value="scan_destination_qty" class="mb-2"/>
                </div>
                <div class="button-list button-vertical-list full mt-10">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn depressed @click="state.on_action_full_bin">
                                Full bin
                            </v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>
            <stock-zero-check
                v-if="state_is('zero_check')"
                v-on:action="state.on_action"
                />
            <batch-picking-line-stock-out
                v-if="state_is('stock_issue')"
                v-on:action="state.on_action"
                :line="state.data"
                />
            <manual-select
                v-if="state_is('manual_selection')"
                v-on:select="state.on_select"
                v-on:back="state.on_back"
                :records="state.data.records"
                :key_value="'id'"
                />

            <!-- TODO: do we need a component for this? -->
            <div class="unload-all" v-if="state_is('unload_all')">
                <v-card outlined class="main">
                    <v-card-title>
                        <div class="main-info">
                            <div class="destination">
                                <span class="label">Destination:</span>
                                {{ state.data.location_dst.name }}
                            </div>
                        </div>
                    </v-card-title>
                </v-card>
            </div>
        </Screen>
    `,
    computed: {
        batch_id: function () {
            return this.erp_data.data.confirm_start.id
        },
    },
    methods: {
        action_full_bin: function () {
            this.go_state(
                'wait_call',
                this.odoo.call('prepare_unload', {
                    'picking_batch_id': this.batch_id,
                })
            )
        },
    },
    data: function () {
        // TODO: add a title to each screen
        return {
            'usage': 'cluster_picking',
            'initial_state_key': 'start',
            'current_state_key': 'start',
            'scan_destination_qty': 1,
            'states': {
                'start': {
                    enter: () => {
                        this.reset_erp_data('data')
                    },
                    on_get_work: (evt) => {
                        this.go_state(
                            'wait_call',
                            this.odoo.call('find_batch')
                        )
                    },
                    on_manual_selection: (evt) => {
                        this.go_state(
                            'wait_call',
                            this.odoo.call('list_batch')
                        )
                    },
                },
                'manual_selection': {
                    on_back: () => {
                        this.go_state('start')
                        this.reset_notification()
                    },
                    on_select: (selected) => {
                        this.go_state(
                            'wait_call',
                            this.odoo.call('select', {
                                'picking_batch_id': selected,
                            })
                        )
                    },
                    display_info: {
                        'title': 'Select a batch and start'
                    },
                },
                'confirm_start': {
                    on_confirm: () => {
                        this.go_state(
                            'wait_call',
                            this.odoo.call('confirm_start', {
                                'picking_batch_id': this.batch_id,
                            })
                        )
                    },
                    on_cancel: () => {
                        this.go_state(
                            'wait_call',
                            this.odoo.call('unassign', {
                                'picking_batch_id': this.batch_id,
                            })
                        )
                    }
                },
                'start_line': {
                    display_info: {
                        'title': 'Pick the product by scanning something'
                    },
                    scan_placeholder: 'Scan location / pack / product / lot',
                    // here we have to use some info sent back from `select`
                    // or from `find_batch` that we pass to scan line
                    on_scan: (scanned) => {
                        this.go_state(
                            'wait_call',
                            this.odoo.call('scan_line', {
                                'move_line_id': this.state.data.id,
                                'barcode': scanned.text,
                            })
                        )
                    },
                    // additional actions
                    on_action: (action) => {
                        this.state['on_' + action].call(this)
                    },
                    on_action_full_bin: () => {
                        this.action_full_bin()
                    },
                    on_action_skip_line: () => {
                        this.go_state(
                            'wait_call',
                            this.odoo.call('skip_line', {
                                'move_line_id': this.state.data.id,
                            })
                        )
                    },
                    on_action_stock_out: () => {
                        this.state_set_data(this.state.data, 'stock_issue')
                        this.go_state('stock_issue')
                    },
                    on_action_change_pack_or_lot: () => {
                        this.go_state(
                            'wait_call',
                            this.odoo.call('change_pack_lot', {
                                'move_line_id': this.state.data.id,
                            })
                        )
                    },
                },
                'scan_destination': {
                    display_info: {
                        'title': 'Check quantity and scan a destination bin'
                    },
                    scan_placeholder: 'Scan destination bin',
                    enter: () => {
                        // TODO: shalle we hook v-model for qty input straight to the state data?
                        this.scan_destination_qty = this.erp_data.data.start_line.quantity
                    },
                    on_qty_update: (qty) => {
                        this.scan_destination_qty = parseInt(qty)
                    },
                    on_scan: (scanned) => {
                        this.go_state(
                            'wait_call',
                            this.odoo.call('scan_destination_pack', {
                                'move_line_id': this.state.data.id,
                                'barcode': scanned.text,
                                'quantity': this.scan_destination_qty,
                            })
                        )
                    },
                    on_action_full_bin: () => {
                        this.action_full_bin()
                    },
                },
                'zero_check': {
                    on_action: (action) => {
                        this.state['on_' + action].call(this)
                    },
                    on_action_confirm_zero: () => {
                        this.go_state(
                            'wait_call',
                            this.odoo.call('is_zero', {
                                'move_line_id': this.state.data.id,
                                'zero': true
                            })
                        )
                    },
                    on_action_confirm_not_zero: () => {
                        this.go_state(
                            'wait_call',
                            this.odoo.call('is_zero', {
                                'move_line_id': this.state.data.id,
                                'zero': false
                            })
                        )
                    },
                },
                'unload_all': {
                    on_scan: (scanned, confirmation=false) => {
                        this.state_set_data({'location_barcode': scanned.text})
                        this.go_state(
                            'wait_call',
                            this.odoo.call('set_destination_all', {
                                'picking_batch_id': this.batch_id,
                                'barcode': scanned.text,
                                'confirmation': confirmation,
                            })
                        )
                    },
                    on_action_split: () => {
                        this.go_state(
                            'wait_call',
                            this.odoo.call('unload_split', {
                                'picking_batch_id': this.batch_id,
                                'barcode': scanned.text, // TODO: should get barcode -> which one? See py specs
                            })
                        )
                    },
                    scan_placeholder: 'Scan location',
                    display_info: {
                        'title': 'Unload all bins',
                    }
                },
                'confirm_unload_all': {
                    on_user_confirm: (answer) => {
                        // TODO: check if this used
                        //-> no flag is set to enable the confirmation dialog,
                        // we only display a message, unlike `confirm_start`
                        if (answer == 'yes'){
                            // reuse data from unload_all
                            let scan_data = this.state_get_data('unload_all')
                            this.state.on_scan(scan_data.location_barcode, true)
                        } else {
                            this.go_state('scan_location')
                        }
                    },
                    on_scan: (scanned, confirmation=true) => {
                        this.on_exit()
                        this.current_state_key = 'unload_all'
                        this.state.on_scan(scanned, confirmation)
                    },
                    scan_placeholder: 'Unload all: scan location',
                },
                'unload_single': {
                    on_scan: (scanned) => {
                        this.go_state(
                            'wait_call',
                            this.odoo.call('unload_scan_pack', {
                                'package_id': null, // FIXME: where does it come from? backend data?
                                'barcode': scanned.text,
                            })
                        )
                    },
                    scan_placeholder: 'Unload single: scan location',
                },
                'unload_set_destination': {
                    on_scan: (scanned) => {
                        this.go_state(
                            'wait_call',
                            this.odoo.call('unload_scan_destination', {
                                'package_id': null, // FIXME: where does it come from? backend data?
                                'barcode': scanned.text,
                            })
                        )
                    },
                    scan_placeholder: 'Scan location',
                },
                'confirm_unload_set_destination': {
                    on_scan: (scanned) => {
                        this.go_state(
                            'wait_call',
                            this.odoo.call('unload_scan_destination', {
                                'package_id': null, // FIXME: where does it come from? backend data?
                                'barcode': scanned.text,
                                'confirmation': true,
                            })
                        )
                    },
                    scan_placeholder: 'Scan location',
                },
                'show_completion_info': {
                    on_confirm: () => {
                        this.go_state(
                            'wait_call',
                            this.odoo.call('unload_router', {
                                'picking_batch_id': this.batch_id,
                            })
                        )
                    },
                },
                'change_pack_lot': {
                    on_scan: (scanned) => {
                        this.go_state(
                            'wait_call',
                            this.odoo.call('change_pack_lot', {
                                'move_line_id': this.state.data.id,
                                'barcode': scanned.text,
                            })
                        )
                    },
                    scan_placeholder: 'Scan pack or lot',
                },
                'stock_issue': {
                    enter: () => {
                        this.reset_notification()
                    },
                    on_action: (action) => {
                        this.state['on_' + action].call(this)
                    },
                    on_confirm_stock_issue: () => {
                        this.go_state(
                            'wait_call',
                            this.odoo.call('stock_issue', {
                                'move_line_id': this.state.data.id,
                            })
                        )
                    },
                    on_back: () => {
                        this.state_set_data({})
                        this.reset_notification()
                        this.go_state('start_line')
                    },
                },
            }
        }
    },
})
