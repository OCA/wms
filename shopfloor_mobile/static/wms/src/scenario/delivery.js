/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ScenarioBaseMixin} from "/shopfloor_mobile_base/static/wms/src/scenario/mixins.js";
import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

const Delivery = {
    mixins: [ScenarioBaseMixin],
    template: `
        <Screen :screen_info="screen_info">
            <template v-slot:header>
                <state-display-info :info="current_location_msg()" v-if="current_location()"/>
                <state-display-info :info="state.display_info" v-if="state.display_info"/>
            </template>
            <searchbar
                v-if="state.on_scan"
                v-on:found="on_scan"
                :input_placeholder="search_input_placeholder"
                />
            <div v-if="state_in(['deliver', 'confirm_done']) && has_picking()">
                <picking-summary
                    :record="state.data.picking"
                    :records_grouped="deliver_picking_summary_records_grouped(state.data.picking)"
                    :action_cancel_package_key="'package_src'"
                    :list_options="deliver_move_line_list_options(state.data.picking)"
                    :key="make_state_component_key(['picking-summary', 'detail-picking', state.data.picking.id])"
                    />
            </div>
            <div v-if="state_is('manual_selection')">
                <manual-select
                    class="with-progress-bar"
                    :records="state.visible_records(this.state.data.pickings)"
                    :options="manual_select_options()"
                    :key="make_state_component_key(['delivery', 'manual-select'])"
                    />
            </div>
            <div class="button-list button-vertical-list full">
                <v-row align="center" v-if="state_is('deliver') && is_current_location_set()">
                    <v-col class="text-center" cols="12">
                        <btn-action @click="reset_current_location">Reset location</btn-action>
                    </v-col>
                </v-row>
                <v-row align="center" v-if="state_is('deliver') && has_picking()">
                    <v-col class="text-center" cols="12">
                        <btn-action @click="state.on_mark_as_done">Make partial delivery</btn-action>
                    </v-col>
                </v-row>
                <v-row align="center" v-if="state_in([initial_state_key, 'deliver'])">
                    <v-col class="text-center" cols="12">
                        <btn-action @click="state.on_manual_selection">Manual selection</btn-action>
                    </v-col>
                </v-row>
                <v-row align="center" v-if="state_is('confirm_done')">
                    <v-col class="text-center" cols="12">
                        <btn-action action="todo" @click="state.on_confirm">Confirm</btn-action>
                    </v-col>
                </v-row>
                <v-row align="center" v-if="state_in(['confirm_done'])">
                    <v-col class="text-center" cols="12">
                        <btn-back />
                    </v-col>
                </v-row>
            </div>
        </Screen>
        `,
    methods: {
        screen_title: function () {
            if (_.isEmpty(this.current_doc()) || this.state_is(this.initial_state_key))
                return this.menu_item().name;
            return this.current_picking().name;
        },
        current_doc: function () {
            const picking = this.current_picking();
            return {
                record: picking,
                identifier: picking.name,
            };
        },
        current_picking: function () {
            const data = this.state_get_data("deliver");
            if (_.isEmpty(data) || _.isEmpty(data.picking)) {
                return {};
            }
            return data.picking;
        },
        current_location: function () {
            const data = this.state_get_data("deliver");
            if (_.isEmpty(data) || _.isEmpty(data.sublocation)) {
                return {};
            }
            return data.sublocation;
        },
        is_current_location_set: function () {
            return !_.isEmpty(this.current_location());
        },
        reset_current_location: function () {
            this.wait_call(
                this.odoo.call("scan_deliver", {
                    barcode: "",
                    picking_id: this.current_picking().id,
                })
            );
        },
        current_location_msg: function () {
            if (this.current_location().id) {
                return {title: "Working from location " + this.current_location().name};
            }
            return "";
        },
        has_picking: function () {
            return !_.isEmpty(this.current_picking());
        },
        deliver_picking_summary_records_grouped(picking) {
            const self = this;
            return this.utils.wms.group_lines_by_location(picking.move_lines, {
                prepare_records: _.partialRight(
                    this.utils.wms.group_by_pack,
                    "package_src"
                ),
                group_color_maker: function (lines) {
                    return self.utils.wms.move_lines_completeness(lines) == 100
                        ? "screen_step_done"
                        : "screen_step_todo";
                },
            });
        },
        deliver_move_line_list_options: function (picking) {
            return {
                list_item_options: {
                    actions: ["action_cancel_line"],
                    fields: this.move_line_detail_fields(),
                    list_item_klass_maker: this.utils.wms.move_line_color_klass,
                },
            };
        },
        move_line_detail_fields: function () {
            return [{path: "package_src.name", klass: "loud"}];
        },
        manual_select_options: function () {
            return {
                show_title: false,
                showActions: false,
                group_title_default: "Pickings to process",
                group_color: this.utils.colors.color_for("screen_step_todo"),
                list_item_extra_component: "picking-list-item-progress-bar",
                list_item_options: {
                    fields: this.manual_select_picking_fields(),
                },
            };
        },
        manual_select_picking_fields: function () {
            const self = this;
            return [
                {path: "name", klass: "loud", action_val_path: "name"},
                {path: "partner.name"},
                {path: "origin"},
                {
                    path: "move_line_count",
                    label: "Lines",
                    renderer: function (rec, field) {
                        return (
                            self.utils.wms.completed_move_lines(rec.move_lines) +
                            " / " +
                            rec.move_lines.length
                        );
                    },
                },
            ];
        },
        existing_package_select_fields: function () {
            return [
                {path: "weight"},
                {path: "move_line_count", label: "Line count"},
                {path: "packaging.name"},
            ];
        },
    },
    data: function () {
        return {
            usage: "delivery",
            initial_state_key: "select_document",
            states: {
                // TODO: likely we can trash this state and merge it w/ "deliver" (as "confirm_done")
                select_document: {
                    display_info: {
                        title: "Start by scanning something",
                        scan_placeholder: "Scan pack / product / picking / location",
                    },
                    on_scan: (scanned) => {
                        this.wait_call(
                            this.odoo.call("scan_deliver", {barcode: scanned.text})
                        );
                    },
                    on_manual_selection: (evt) => {
                        this.wait_call(this.odoo.call("list_stock_picking"));
                    },
                },
                deliver: {
                    display_info: {
                        title: "Scan another document",
                        scan_placeholder: "Scan pack / product / picking / location",
                    },
                    events: {
                        cancel_picking_line: "on_cancel",
                    },
                    on_scan: (scanned) => {
                        this.wait_call(
                            this.odoo.call("scan_deliver", {
                                barcode: scanned.text,
                                picking_id: this.current_picking().id,
                                location_id: this.current_location().id,
                            })
                        );
                    },
                    on_manual_selection: (evt) => {
                        this.wait_call(
                            this.odoo.call("list_stock_picking", {
                                location_id: this.current_location().id,
                            })
                        );
                    },
                    on_cancel: (data) => {
                        let endpoint, endpoint_data;
                        // TODO: can't we have a single endpoint as per checkout.summary.destroy?
                        if (data.package_id) {
                            endpoint = "reset_qty_done_pack";
                            endpoint_data = {
                                package_id: data.package_id,
                                picking_id: this.current_picking().id,
                            };
                        } else {
                            endpoint = "reset_qty_done_line";
                            endpoint_data = {
                                move_line_id: data.line_id,
                                picking_id: this.current_picking().id,
                            };
                        }
                        this.wait_call(this.odoo.call(endpoint, endpoint_data));
                    },
                    on_mark_as_done: () => {
                        this.wait_call(
                            this.odoo.call("done", {
                                picking_id: this.current_picking().id,
                            })
                        );
                    },
                },
                manual_selection: {
                    display_info: {
                        title: "Scan a document or select it",
                        scan_placeholder: "Filter this list by name search",
                    },
                    events: {
                        select: "on_select",
                        go_back: "on_back",
                    },
                    on_scan: (scanned) => {
                        this.state_set_data({filtered: scanned.text});
                    },
                    on_back: () => {
                        this.state_to("start");
                        this.reset_notification();
                    },
                    on_select: (selected) => {
                        this.wait_call(
                            this.odoo.call("scan_deliver", {barcode: selected.name})
                        );
                    },
                    visible_records: (records) => {
                        const self = this;
                        let visible_records = this.utils.wms.order_picking_by_completeness(
                            records
                        );
                        if (this.state.data.filtered) {
                            visible_records = _.filter(visible_records, function (rec) {
                                return rec.name.search(self.state.data.filtered) > 0;
                            });
                        }
                        return visible_records;
                    },
                },
                // TODO: likely we don't need this state as we could handle this in "deliver"
                confirm_done: {
                    display_info: {
                        title: "Confirm done",
                    },
                    events: {
                        go_back: "on_back",
                    },
                    on_confirm: () => {
                        this.wait_call(
                            this.odoo.call("done", {
                                picking_id: this.current_picking().id,
                                confirm: true,
                            })
                        );
                    },
                    on_back: () => {
                        this.reset_notification();
                    },
                },
            },
        };
    },
};

process_registry.add("delivery", Delivery);

export default Delivery;
