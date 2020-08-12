import {ScenarioBaseMixin} from "./mixins.js";
import {process_registry} from "../services/process_registry.js";

export var SinglePackStatesMixin = {
    data: function() {
        return {
            states: {
                // Generic state for when to start w/ scanning a pack
                start_scan_pack: {
                    display_info: {
                        title: "Start by scanning a pack",
                        scan_placeholder: "Scan pack",
                    },
                    enter: () => {
                        this.state_reset_data();
                    },
                    on_scan: scanned => {
                        this.wait_call(
                            this.odoo.call("start", {barcode: scanned.text})
                        );
                    },
                },
                // Generic state for when to start w/ scanning a pack or loc
                start_scan_pack_or_location: {
                    display_info: {
                        title: "Start by scanning a pack or a location",
                        scan_placeholder: "Scan pack",
                    },
                    enter: () => {
                        this.state_reset_data();
                    },
                    on_scan: scanned => {
                        this.wait_call(
                            this.odoo.call("start", {barcode: scanned.text})
                        );
                    },
                },
                // TODO: these states should be splitted out to a specific mixin
                // for putaway and pack transfer
                scan_location: {
                    display_info: {
                        title: "Set a location",
                        scan_placeholder: "Scan location",
                        show_cancel_button: true,
                    },
                    on_scan: (scanned, confirmation = false) => {
                        this.state_set_data({location_barcode: scanned.text});
                        this.wait_call(
                            this.odoo.call("validate", {
                                package_level_id: this.state.data.id,
                                location_barcode: scanned.text,
                                confirmation: confirmation,
                            })
                        );
                    },
                    on_cancel: () => {
                        this.wait_call(
                            this.odoo.call("cancel", {
                                package_level_id: this.state.data.id,
                            })
                        );
                    },
                },
                confirm_location: {
                    display_info: {
                        scan_placeholder: "Scan location",
                    },
                    enter: () => {
                        this.need_confirmation = true;
                    },
                    exit: () => {
                        this.need_confirmation = false;
                    },
                    on_user_confirm: answer => {
                        if (answer == "yes") {
                            // Reuse data from scan_location and
                            // simulate the event that on_scan expects
                            const scan_data = this.state_get_data("scan_location");
                            this.state.on_scan(
                                {
                                    text: scan_data.location_barcode,
                                },
                                true
                            );
                        } else {
                            this.state_to("scan_location");
                        }
                    },
                    on_scan: (scanned, confirmation = true) => {
                        this.on_state_exit();
                        // FIXME: use state_load
                        this.current_state_key = "scan_location";
                        this.state.on_scan(scanned, confirmation);
                    },
                },
                confirm_start: {
                    display_info: {
                        title: "Confirm start and select a location",
                        scan_placeholder: "Scan location",
                    },
                    enter: () => {
                        this.need_confirmation = true;
                    },
                    exit: () => {
                        this.need_confirmation = false;
                    },
                    on_user_confirm: answer => {
                        if (answer == "yes") {
                            // Keep the data received from previous state but not the question answered
                            const state_data = this.state_get_data(
                                this.current_state_key
                            );
                            state_data.message = {};
                            this.state_set_data(state_data, "scan_location");
                            this.state_to("scan_location");
                        } else {
                            this.state_to("start");
                        }
                    },
                    on_scan: scanned => {
                        this.on_state_exit();
                        this.current_state_key = "scan_location";
                        this.state.on_scan(scanned);
                    },
                },
            },
        };
    },
};

export var SinglePackTransfer = Vue.component("single-pack-transfer", {
    mixins: [ScenarioBaseMixin, SinglePackStatesMixin],
    template: `
        <Screen :screen_info="screen_info">
            <template v-slot:header>
                <state-display-info :info="state.display_info" v-if="state.display_info"/>
            </template>
            <searchbar v-if="state_is(initial_state_key)" v-on:found="on_scan" :input_placeholder="search_input_placeholder"></searchbar>
            <searchbar v-if="state_is('scan_location')" v-on:found="on_scan" :input_placeholder="search_input_placeholder" :input_data_type="'location'"></searchbar>
            <user-confirmation v-if="need_confirmation" v-on:user-confirmation="on_user_confirm" v-bind:question="user_notification.message"></user-confirmation>
            <detail-operation v-if="state.key != initial_state_key && state.key != 'show_completion_info'" :record="state.data" />
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
process_registry.add("single_pack_transfer", SinglePackTransfer, {
    demo_src: "demo/demo.single_pack_transfer.js",
});
