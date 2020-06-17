import {ScenarioBaseMixin} from "./mixins.js";
import {process_registry} from "../services/process_registry.js";
import {demotools} from "../demo/demo.core.js"; // FIXME: dev only
import {} from "../demo/demo.delivery.js"; // FIXME: dev only

export var LocationContentTransfer = Vue.component("checkout", {
    mixins: [ScenarioBaseMixin],
    template: `
        <Screen :screen_info="screen_info">
            <template v-slot:header>
                <state-display-info :info="state.display_info" v-if="state.display_info"/>
            </template>
            <searchbar
                v-if="state.on_scan"
                v-on:found="on_scan"
                :input_placeholder="search_input_placeholder"
                />
            <div v-if="state_is('start_recovered') && has_picking()">
                <detail-picking
                    :key="make_state_component_key(['picking'])"
                    :record="state.data.move_line.picking"
                    :options="{main: true}"
                    />
                <batch-picking-line-detail
                    :line="state.data.move_line"
                    :show-qty-picker="true"
                    />
            </div>
        </Screen>
        `,
    // FIXME: just for dev
    // mounted: function() {
    //     // TEST force state and data
    //     const state = "select_package";
    //     const dcase = demotools.get_case(this.usage);
    //     const data = dcase["select_package"].data[state];
    //     this.state_set_data(data, state);
    //     this._state_load(state);
    // },
    methods: {
        screen_title: function() {
            if (_.isEmpty(this.current_doc()) || this.state_is(this.initial_state_key))
                return this.menu_item().name;
            return this.current_picking().name;
        },
        current_doc: function() {
            const picking = this.current_picking();
            return {
                record: picking,
                identifier: picking.name,
            };
        },
        current_picking: function() {
            const data = this.state_get_data("start_recovered");
            if (_.isEmpty(data) || _.isEmpty(data.move_line.picking)) {
                return {};
            }
            return data.move_line.picking;
        },
        has_picking: function() {
            return !_.isEmpty(this.current_picking());
        },
    },
    data: function() {
        const self = this;
        return {
            usage: "location_content_transfer",
            initial_state_key: "start",
            states: {
                start: {
                    enter: () => {
                        this.state_reset_data();
                        this.wait_call(this.odoo.call("start_or_recover"));
                    },
                    on_scan: scanned => {
                        this.wait_call(this.odoo.call("TODO", {barcode: scanned.text}));
                    },
                },
                /**
                 * TODO: this state could be useless
                as we should use only one state to start
                but we cannot use "start"
                as it's aliased as the initial state automatically.

                */
                start_recovered: {
                    display_info: {
                        scan_placeholder: "Scan pack / product / lot",
                    },
                    on_scan: scanned => {
                        this.wait_call(this.odoo.call("TODO", {barcode: scanned.text}));
                    },
                },
                scan_location: {
                    display_info: {
                        title: "Start by scanning a location",
                        scan_placeholder: "Scan location",
                    },
                    on_scan: scanned => {
                        this.wait_call(this.odoo.call("TODO", {barcode: scanned.text}));
                    },
                },
            },
        };
    },
});

process_registry.add("location_content_transfer", LocationContentTransfer);
