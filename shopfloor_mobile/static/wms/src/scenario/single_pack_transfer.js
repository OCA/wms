import {ScenarioBaseMixin, GenericStatesMixin} from "./mixins.js";

Vue.component('single-pack-transfer', {
    mixins: [ScenarioBaseMixin, GenericStatesMixin],
    template: `
        <Screen title="Single pack transfer">
            <!-- FOR DEBUG -->
            <!-- {{ current_state }} -->
            <searchbar v-if="current_state == 'scan_anything'" v-on:found="scanned" :input_placeholder="search_input_placeholder"></searchbar>
            <searchbar v-if="current_state == 'scan_pack'" v-on:found="scanned" :input_placeholder="state['scan_pack'].scan_placeholder" :input_data_type="'pack'"></searchbar>
            <searchbar v-if="current_state == 'scan_location'" v-on:found="scanned" :input_placeholder="state['scan_location'].scan_placeholder" :input_data_type="'location'"></searchbar>
            <user-information v-if="!need_confirmation && user_notification.message" v-bind:info="user_notification"></user-information>
            <user-confirmation v-if="need_confirmation" v-on:user-confirmation="onUserConfirmation" v-bind:question="user_notification.message"></user-confirmation>
            <operation-detail :operation="erp_data.data"></operation-detail>
            <last-operation v-if="current_state == 'last_operation'" v-on:confirm="state['last_operation'].on_confirm"></last-operation>
            <reset-screen-button v-on:reset="on_reset" :show_reset_button="show_reset_button"></reset-screen-button>
        </Screen>
    `,
    data: function () {
        return {
            'usage': 'single_pack_transfer',
            'show_reset_button': true,
            'initial_state': 'scan_anything',
            'current_state': 'scan_anything',
            'state': {
                'scan_anything': {
                    enter: () => {
                        this.reset_erp_data('data')
                    },
                    on_scan: (scanned) => {
                        // let scan_it = scanned.type == 'pack' ? this.odoo.scan_pack : this.odoo.scan_location
                        // this.go_state('wait_scan_anything', scan_it.call(this.odoo, scanned.text))
                        this.go_state('wait_scan_anything', this.odoo.scan_anything(scanned.text))
                    },
                    scan_placeholder: 'Scan anything...',
                },
                'wait_scan_anything': {
                    success: (result) => {
                        let next_state = 'scan_anything'
                        if (!_.isUndefined(result.data)) {
                            this.set_erp_data('data', result.data)
                            if (result.data.type == 'pack')
                                next_state = 'scan_location'
                        }
                        this.go_state(next_state)
                    },
                    error: (result) => {
                        this.go_state('scan_anything')
                    },
                },
                'last_operation': {
                    on_confirm: () => {
                        this.go_state('start')
                    },
                },
            }
        }
    },
})
