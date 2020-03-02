import {GenericStatesMixin, ScenarioBaseMixin, SinglePackStatesMixin} from "./mixins.js";

export var SinglePackPutAway = Vue.component('single-pack-putaway', {
    mixins: [ScenarioBaseMixin, GenericStatesMixin, SinglePackStatesMixin],
    template: `
        <Screen :title="menuItem.name" :klass="usage">
            <template v-slot:header>
                <user-information
                    v-if="!need_confirmation && user_notification.message"
                    v-bind:info="user_notification"
                    />
                <state-display-info :info="state.display_info" v-if="state.display_info"/>
            </template>
            <searchbar v-on:found="on_scan" :input_placeholder="search_input_placeholder"></searchbar>
            <user-confirmation v-if="need_confirmation" v-on:user-confirmation="on_user_confirm" v-bind:question="user_notification.message"></user-confirmation>
            <operation-detail :operation="state.data"></operation-detail>
            <cancel-button v-on:cancel="on_cancel" v-if="show_cancel_button"></cancel-button>
        </Screen>
    `,
    data: function () {
        return {
            'usage': 'single_pack_putaway',
            'show_reset_button': true,
            // FIXME: scenario has changed -> we should use `start_scan_pack_or_location` as on pack transfer
            'initial_state_key': 'start_scan_pack',
            'current_state_key': 'start_scan_pack',
        };
    },
});
