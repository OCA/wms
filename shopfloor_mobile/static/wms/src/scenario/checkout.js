/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ScenarioBaseMixin} from "/shopfloor_mobile_base/static/wms/src/scenario/mixins.js";
import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";
import {checkout_states} from "./checkout_states.js";
import event_hub from "/shopfloor_mobile_base/static/wms/src/services/event_hub.js";

const Checkout = {
    mixins: [ScenarioBaseMixin],
    /*
        /!\ IMPORTANT: we use many times the same component
        (eg: manual-select or detail-picking-select)
        and to make sure they don't get cached together
        we MUST call them using `:key` to make them unique!
        If you don't, you'll have severe problems of data being shared
        between each instances. This is the real problem:
        you assume to have different instance but indeed you get only 1
        which is reused every time!
    */
    template: `
        <Screen :screen_info="screen_info">
            <template v-slot:header>
                <state-display-info :info="state.display_info" v-if="state.display_info"/>
            </template>
            <searchbar
                v-show="state.on_scan"
                v-on:found="on_scan"
                :input_placeholder="search_input_placeholder"
                />
            <div v-if="state_is('select_document')">
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-action @click="state.on_manual_selection">Manual selection</btn-action>
                        </v-col>
                    </v-row>
                </div>
            </div>
            <div v-if="state_is('manual_selection')">
                <manual-select
                    :records="state.data.pickings"
                    :options="manual_selection_manual_select_options()"
                    :key="make_state_component_key(['checkout', 'manual-select'])"
                    />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-back />
                        </v-col>
                    </v-row>
                </div>
            </div>
            <div v-if="state_is('select_line')">
                <item-detail-card
                    v-if="current_carrier()"
                    :card_color="utils.colors.color_for('detail_carrier_card')"
                    :key="make_state_component_key(['picking-carrier', state.data.picking.id])"
                    :record="current_carrier()"
                    :options="{main: true, key_title: 'name', title_icon: 'mdi-truck-outline'}"
                    />
                <detail-picking-select
                    v-bind="select_line_detail_picking_select_props()"
                    :key="make_state_component_key(['detail-picking-select'])"
                    />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-action @click="$root.trigger('summary')">Summary</btn-action>
                        </v-col>
                    </v-row>
                </div>
            </div>

            <div v-if="state_is('select_package')">
                <v-alert type="info" tile v-if="state.data.picking.note" class="packing-info">
                    <p v-text="state.data.picking.note" />
                </v-alert>
                <item-detail-card
                    v-if="state.data.picking.carrier"
                    :key="make_state_component_key(['picking-carrier', state.data.picking.id])"
                    :record="state.data.picking.carrier"
                    :options="{main: true, key_title: 'name', title_icon: 'mdi-truck-outline'}"
                    />
                <detail-picking-select
                    :record="state.data.picking"
                    :select_records="state.data.selected_move_lines"
                    :select_options="select_package_manual_select_opts()"
                    :key="make_state_component_key(['detail-picking-select'])"
                    />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-action
                                   @click="state.on_existing_pack"
                                   :disabled="_.isEmpty(selected_lines())"
                                   >Existing pack</btn-action>
                        </v-col>
                    </v-row>
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-action
                                   @click="state.on_new_pack"
                                   :disabled="_.isEmpty(selected_lines())"
                                   >New pack</btn-action>
                        </v-col>
                    </v-row>
                    <v-row align="center" v-if="state.data.no_package_enabled">
                        <v-col class="text-center" cols="12">
                            <btn-action
                                   @click="state.on_without_pack"
                                   :disabled="_.isEmpty(selected_lines())"
                                   >Process w/o pack</btn-action>
                        </v-col>
                    </v-row>
                </div>
            </div>
            <div v-if="state_is('select_delivery_packaging')">
                <item-detail-card
                    v-if="current_doc().record.carrier"
                    :key="make_state_component_key(['picking-carrier', current_doc().record.id])"
                    :record="current_doc().record.carrier"
                    :options="{main: true, key_title: 'name', title_icon: 'mdi-truck-outline'}"
                    />
                <manual-select
                    :records="state.data.packaging"
                    :options="select_delivery_packaging_manual_select_options()"
                    :key="make_state_component_key(['checkout', 'select-delivery-packaging'])"
                    />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-back />
                        </v-col>
                    </v-row>
                </div>
            </div>
            <div v-if="state_is('select_dest_package')">
                <detail-picking-select
                    :record="state.data.picking"
                    :select_records="state.data.packages"
                    :select_options="{list_item_fields: existing_package_select_fields, list_item_component: 'list-item'}"
                    :key="make_state_component_key(['detail-picking-select'])"
                    />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-back />
                        </v-col>
                    </v-row>
                </div>
            </div>
            <div v-if="state_is('change_quantity')">
                <item-detail-card :card_color="utils.colors.color_for('screen_step_done')"
                    :key="make_state_component_key(['location_src'])"
                    :record="state.data.line"
                :options="{main: true, key_title: 'location_src.name', title_action_field: {action_val_path: 'location_src.barcode'}, }"
                    />
                <item-detail-card :card_color="utils.colors.color_for('screen_step_done')"
                    :key="make_state_component_key(['product'])"
                    :record="state.data.line"
                    :options="utils.wms.move_line_product_detail_options(state.data.line, {fields_blacklist: ['quantity']})"
                    />
                <v-card class="pa-2" :color="utils.colors.color_for('screen_step_todo')">
                    <packaging-qty-picker
                        :key="make_state_component_key(['packaging-qty-picker', state.data.line.id])"
                        v-bind="utils.wms.move_line_qty_picker_props(state.data.line)"
                        />
                </v-card>
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-action @click="$root.trigger('qty_change_confirm')">Confirm</btn-action>
                        </v-col>
                    </v-row>
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn color="default" @click="state.on_back">Back</v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>
            <div v-if="state_is('change_packaging')">
                <detail-picking-select
                    :record="state.data.picking"
                    :select_records="state.data.packaging"
                    :select_options="{list_item_component: 'list-item'}"
                    :key="make_state_component_key(['detail-picking-select'])"
                    />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-back />
                        </v-col>
                    </v-row>
                </div>
            </div>
            <div v-if="state_is('summary')">
                <picking-summary
                    :record="state.data.picking"
                    :records_grouped="utils.wms.group_lines_by_location(state.data.picking.move_lines, {'group_key': 'location_dest', 'prepare_records': utils.wms.group_by_pack})"
                    :list_options="{list_item_options: {actions: ['action_change_pkg', 'action_cancel_line']}}"
                    :key="make_state_component_key(['picking-summary'])"
                    />
                <div class="button-list button-vertical-list full">
                    <v-row align="center" v-if="!state.data.all_processed">
                        <v-col class="text-center" cols="12">
                            <btn-action @click="$root.trigger('continue')">Continue checkout</btn-action>
                        </v-col>
                    </v-row>
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-action action="todo"
                                @click="$root.trigger('mark_as_done')"
                                :disabled="state.data.picking.move_lines.length < 1">Mark as done</btn-action>
                        </v-col>
                    </v-row>
                </div>
            </div>
            <div v-if="state_is('confirm_done')">
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-action action="todo" @click="state.on_confirm">Confirm</btn-action>
                        </v-col>
                    </v-row>
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-back />
                        </v-col>
                    </v-row>
                </div>
            </div>
            <div v-if="state_is('select_child_location')">
                <item-detail-card
                    :key="make_state_component_key(['picking'])"
                    :record="state.data.picking"
                    :options="{key_title: 'location_dest.name'}"
                    :card_color="utils.colors.color_for('screen_step_todo')"
                />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-back />
                        </v-col>
                    </v-row>
                </div>
            </div>
        </Screen>
        `,
    computed: {
        existing_package_select_fields: function () {
            return [
                {path: "weight"},
                {path: "move_line_count", label: "Line count"},
                {path: "packaging.name"},
            ];
        },
    },
    methods: {
        current_carrier: function () {
            return (
                this.state.data.picking.carrier || this.state.data.picking.ship_carrier
            );
        },
        screen_title: function () {
            if (_.isEmpty(this.current_doc()) || this.state_is("confirm_start"))
                return this.menu_item().name;
            const title = this.current_doc().record.name;
            return title;
        },
        current_doc: function () {
            const data = this.state_get_data("select_line");
            if (_.isEmpty(data)) {
                return null;
            }
            return {
                record: data.picking,
                identifier: data.picking.name,
            };
        },
        manual_selection_manual_select_options: function () {
            return {
                group_title_default: "Pickings to process",
                group_color: this.utils.colors.color_for("screen_step_todo"),
                list_item_options: {
                    loud_title: true,
                    fields: [
                        {path: "partner.name"},
                        {path: "origin"},
                        {path: "carrier.name", label: "Carrier"},
                        {path: "move_line_count", label: "Lines"},
                        {
                            path: "priority",
                            render_component: "priority-widget",
                            render_options: function (record) {
                                const priority = parseInt(record.priority);
                                // We need to pass the label to the component as an option instead of using "display_no_value"
                                // because pickings with no priority will still have a string value of "0"
                                // and the label would always be displayed.
                                return {
                                    priority,
                                    label: priority ? "Priority: " : null,
                                };
                            },
                        },
                    ],
                },
            };
        },
        handle_manual_select_highlight_on_scan: function (res) {
            // We need to ensure that the highlights of the detail-picking-select
            // are updated correctly on scan.
            const move_lines_data = this.get_move_lines_data(res);
            move_lines_data.forEach((line) => {
                let checked = false;
                if (line.qty_done > 0) {
                    checked = true;
                }
                event_hub.$emit("manual_select:select_item", {
                    rec_id: line.id,
                    checked,
                });
            });
        },
        get_move_lines_data: function (res) {
            // We need to access the data object to find the move lines,
            // and this path will vary depending on the current screen.
            const data = res.data;
            const state_key = res.next_state;
            const path = this.get_move_lines_path(state_key);
            return _.result(data, path, []);
        },
        get_move_lines_path: function (key) {
            const possible_paths = {
                summary: "picking.move_lines",
                select_line: "picking.move_lines",
                select_package: "selected_move_lines",
                select_dest_package: "selected_move_lines",
            };
            return key + "." + possible_paths[key];
        },
        select_delivery_packaging_manual_select_options: function () {
            return {
                showActions: false,
            };
        },
        select_line_detail_picking_select_props: function () {
            const picking = this.state.data.picking;
            const lines = picking.move_lines;
            let grouped_lines = undefined;
            if (this.state.data.group_lines_by_location) {
                grouped_lines = this.select_line_manual_select_group_lines(lines);
            }
            return {
                record: picking,
                select_records: lines,
                select_records_grouped: grouped_lines,
                select_options: this.select_line_manual_select_opts(),
            };
        },
        select_line_manual_select_group_lines: function (lines) {
            return this.utils.wms.group_lines_by_location(lines, {
                prepare_records: this.utils.wms.only_one_package,
            });
        },
        select_line_manual_select_opts: function () {
            return {
                group_color: this.utils.colors.color_for("screen_step_todo"),
                card_klass: "loud-labels",
                list_item_options: {
                    show_oneline_package_content: this.state.data
                        .show_oneline_package_content,
                },
            };
        },
        select_package_manual_select_opts: function () {
            return {
                multiple: true,
                initValue: this.selected_line_ids(),
                card_klass: "loud-labels",
                list_item_component: "picking-select-package-content",
                list_item_options: {actions: ["action_qty_edit"]},
            };
        },
        selectable_lines: function () {
            const stored = this.state_get_data("select_package");
            return _.result(stored, "selected_move_lines", []);
        },
        selectable_line_ids: function () {
            return this.selectable_lines().map(_.property("id"));
        },
        selected_lines: function () {
            return this.selectable_lines().filter(function (x) {
                return x.qty_done > 0;
            });
        },
        selected_line_ids: function () {
            return this.selected_lines().map(_.property("id"));
        },
        _get_states: function () {
            return checkout_states(this);
        },
    },
    data: function () {
        return {
            usage: "checkout",
            initial_state_key: "select_document",
            states: this._get_states(),
        };
    },
};

process_registry.add("checkout", Checkout);

export default Checkout;
