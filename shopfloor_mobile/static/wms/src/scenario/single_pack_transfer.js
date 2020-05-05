import {ScenarioBaseMixin, SinglePackStatesMixin} from "./mixins.js";
import {process_registry} from "../services/process_registry.js";

export var SinglePackTransfer = Vue.component("single-pack-transfer", {
    mixins: [ScenarioBaseMixin, SinglePackStatesMixin],
    template: `
        <Screen :title="screen_info.title" :klass="screen_info.klass">
            <template v-slot:header>
                <user-information
                    v-if="!need_confirmation && user_notification.message"
                    v-bind:info="user_notification"
                    />
                <state-display-info :info="state.display_info" v-if="state.display_info"/>
            </template>
            <searchbar v-if="state_is(initial_state_key)" v-on:found="on_scan" :input_placeholder="search_input_placeholder"></searchbar>
            <searchbar v-if="state_is('scan_location')" v-on:found="on_scan" :input_placeholder="search_input_placeholder" :input_data_type="'location'"></searchbar>
            <user-confirmation v-if="need_confirmation" v-on:user-confirmation="on_user_confirm" v-bind:question="user_notification.message"></user-confirmation>
            <detail-operation v-if="state.key != initial_state_key" :record="state.data" />
            <last-operation v-if="state_is('show_completion_info')" v-on:confirm="state.on_confirm"></last-operation>
            <cancel-button v-on:cancel="on_cancel" v-if="show_cancel_button"></cancel-button>
        </Screen>
    `,
    data: function() {
        return {
            usage: "single_pack_transfer",
            show_reset_button: true,
            initial_state_key: "start_scan_pack_or_location",
            states: {
                show_completion_info: {
                    on_confirm: () => {
                        // TODO: turn the cone?
                        this.state_to("start");
                    },
                },
            },
        };
    },
});
process_registry.add("single_pack_transfer", SinglePackTransfer);
