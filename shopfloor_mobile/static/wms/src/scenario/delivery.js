import {ScenarioBaseMixin} from "./mixins.js";
import {process_registry} from "../services/process_registry.js";
import {utils} from "../utils.js";
import {demotools} from "../demo/demo.core.js"; // FIXME: dev only
import {} from "../demo/demo.delivery.js"; // FIXME: dev only

export var Delivery = Vue.component("checkout", {
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
            <div v-if="state_is(initial_state_key)">
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn depressed color="primary" @click="state.on_manual_selection">Manual selection</v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>
            <div v-if="state_is('deliver')">
                <picking-summary
                    :picking="state.data.picking"
                    :records_grouped="utils.group_lines_by_location(state.data.picking.move_lines, {'prepare_records': utils.group_by_pack})"
                    :list_options="deliver_move_line_list_options()"
                    :key="current_state_key + '-detail-picking-' + state.data.picking.id"
                    />
                <hr />
                <!--
                TEST DETAIL + LIST
                <detail-picking
                    :picking="state.data.picking"
                    :key="current_state_key + '-detail-picking-' + state.data.picking.id + 2"
                    />
                <list
                    :records="state.data.picking.move_lines"
                    :grouped_records="utils.group_lines_by_location(state.data.picking.move_lines, {'prepare_records': utils.only_one_package})"
                    :options="deliver_move_line_list_options()"
                    :key="current_state_key + '-detail-picking-select'"
                    />
                -->
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn depressed color="primary" @click="state.on_manual_selection">Manual selection</v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>
            <div v-if="state_is('manual_selection')">
                <manual-select
                    :records="state.data.pickings"
                    :options="{showActions: false}"
                    :list_item_fields="manual_select_picking_fields"
                    :key="current_state_key + '-manual-select'"
                    />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn depressed color="default" @click="state.on_back">Back</v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>
        </Screen>
        `,
    computed: {
        utils: function() {
            return utils;
        },
        // TODO: move these to methods
        manual_select_picking_fields: function() {
            return [
                {path: "partner.name"},
                {path: "origin"},
                {path: "move_line_count", label: "Lines"},
            ];
        },
        existing_package_select_fields: function() {
            return [
                {path: "weight"},
                {path: "move_line_count", label: "Line count"},
                {path: "packaging.name"},
            ];
        },
    },
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
        record_by_id: function(records, _id) {
            // TODO: double check when the process is done if this is still needed or not.
            // `manual-select` can now buble up events w/ full record.
            return _.first(_.filter(records, {id: _id}));
        },
        deliver_move_line_list_options: function() {
            return {
                list_item_options: {
                    actions: ["action_cancel_line"],
                    fields: this.move_line_detail_fields(),
                    list_item_klass_maker: this.utils.move_line_color_klass,
                },
            };
        },
        move_line_detail_fields: function() {
            return [{path: "package_src.name", klass: "loud"}];
        },
    },
    data: function() {
        return {
            usage: "delivery",
            initial_state_key: "select_document",
            states: {
                select_document: {
                    display_info: {
                        title: "Start by scanning something",
                        scan_placeholder: "Scan pack / picking",
                    },
                    enter: () => {
                        this.state_reset_data();
                    },
                    on_scan: scanned => {
                        this.wait_call(
                            this.odoo.call("scan_deliver", {barcode: scanned.text})
                        );
                    },
                    on_manual_selection: evt => {
                        this.wait_call(this.odoo.call("list_stock_picking"));
                    },
                },
                deliver: {
                    display_info: {
                        title: "Scan another document",
                        scan_placeholder: "Scan pack / picking",
                    },
                    events: {
                        cancel_picking_line: "on_cancel",
                    },
                    on_scan: scanned => {
                        this.wait_call(
                            this.odoo.call("scan_deliver", {barcode: scanned.text})
                        );
                    },
                    on_manual_selection: evt => {
                        this.wait_call(this.odoo.call("list_stock_picking"));
                    },
                    on_cancel: data => {
                        let endpoint, endpoint_data;
                        // TODO: can't we have a single endpoint as per checkout.summary.destroy?
                        if (data.package_id) {
                            endpoint = "reset_qty_done_package";
                            endpoint_data = {
                                package_id: data.package_id,
                            };
                        } else {
                            endpoint = "reset_qty_done_line";
                            endpoint_data = {
                                line_id: data.line_id,
                            };
                        }
                        console.log("TODO: call", endpoint, endpoint_data);
                        // this.wait_call(
                        //     this.odoo.call(endpoint, endpoint_data)
                        // );
                    },
                },
                manual_selection: {
                    display_info: {
                        title: "Select a picking and start",
                    },
                    events: {
                        select: "on_select",
                    },
                    on_scan: scanned => {
                        console.log("TODO: filter results");
                    },
                    on_back: () => {
                        this.state_to("start");
                        this.reset_notification();
                    },
                    on_select: selected => {
                        this.wait_call(
                            this.odoo.call("scan_deliver", {barcode: selected.name})
                        );
                    },
                },
            },
        };
    },
});

process_registry.add("delivery", Delivery);
