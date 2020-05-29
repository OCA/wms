import {ScenarioBaseMixin} from "./mixins.js";
import {process_registry} from "../services/process_registry.js";
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
                :reset_on_submit="false"
                />
            <div v-if="state_is(initial_state_key)">
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn color="primary" @click="state.on_manual_selection">Manual selection</v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>
            <div v-if="state_is('deliver')">
                <picking-summary
                    :record="state.data.picking"
                    :records_grouped="utils.misc.group_lines_by_location(state.data.picking.move_lines, {'prepare_records': utils.misc.group_by_pack})"
                    :list_options="deliver_move_line_list_options()"
                    :key="current_state_key + '-detail-picking-' + state.data.picking.id"
                    />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn color="primary" @click="state.on_manual_selection">Manual selection</v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>
            <div v-if="state_is('manual_selection')">
                <manual-select
                    class="with-progress-bar"
                    :records="state.visible_records(this.state.data.pickings)"
                    :options="{show_title: false, showActions: false, list_item_extra_component: 'picking-list-item-progress-bar'}"
                    :list_item_fields="manual_select_picking_fields()"
                    :key="current_state_key + '-manual-select'"
                    />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn color="default" @click="state.on_back">Back</v-btn>
                        </v-col>
                    </v-row>
                </div>
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
        deliver_move_line_list_options: function() {
            return {
                list_item_options: {
                    actions: ["action_cancel_line"],
                    fields: this.move_line_detail_fields(),
                    list_item_klass_maker: this.utils.misc.move_line_color_klass,
                },
            };
        },
        move_line_detail_fields: function() {
            return [{path: "package_src.name", klass: "loud"}];
        },
        manual_select_picking_fields: function() {
            const self = this;
            return [
                {path: "name", klass: "loud", action_val_path: "name"},
                {path: "partner.name"},
                {path: "origin"},
                {
                    path: "move_line_count",
                    label: "Lines",
                    renderer: function(rec, field) {
                        return (
                            self.utils.misc.picking_completed_lines(rec) +
                            " / " +
                            rec.move_lines.length
                        );
                    },
                },
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
                            endpoint = "reset_qty_done_pack";
                            endpoint_data = {
                                package_id: data.package_id,
                            };
                        } else {
                            endpoint = "reset_qty_done_line";
                            endpoint_data = {
                                line_id: data.line_id,
                            };
                        }
                        this.wait_call(this.odoo.call(endpoint, endpoint_data));
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
                        this.state_set_data({filtered: scanned.text});
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
                    visible_records: records => {
                        const self = this;
                        let visible_records = this.utils.misc.order_picking_by_completeness(
                            records
                        );
                        if (this.state.data.filtered) {
                            visible_records = _.filter(visible_records, function(rec) {
                                return rec.name.search(self.state.data.filtered) > 0;
                            });
                        }
                        return visible_records;
                    },
                },
            },
        };
    },
});

process_registry.add("delivery", Delivery);
