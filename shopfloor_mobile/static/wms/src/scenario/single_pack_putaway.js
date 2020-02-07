import {ScenarioBaseMixin, GenericStatesMixin} from "./mixins.js";

Vue.component('single-pack-putaway', {
    mixins: [ScenarioBaseMixin, GenericStatesMixin],
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
        }
    },
})
