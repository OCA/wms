/**
 * Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
 * Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
 */

import {ScenarioBaseMixin} from "/shopfloor_mobile_base/static/wms/src/scenario/mixins.js";
import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";
import event_hub from "/shopfloor_mobile_base/static/wms/src/services/event_hub.js";
import {reception_states} from "./reception_states.js";

const Reception = {
    mixins: [ScenarioBaseMixin],
    template: `
        <Screen :screen_info="screen_info">
            <template v-slot:header>
                <state-display-info :info="state.display_info" v-if="state.display_info"/>
            </template>
            <searchbar
                v-if="state_in(['select_document', 'select_move', 'set_lot', 'set_quantity', 'set_destination', 'select_dest_package'])"
                v-on:found="on_scan"
                :input_placeholder="search_input_placeholder"
            />
            <date-picker-input
                v-if="state_is('set_lot')"
                :handler_to_update_date="get_expiration_date_from_lot"
                v-on:date_picker_selected="state.on_date_picker_selected"
            />
            <template v-if="state_is('select_move')">
                <item-detail-card
                    :record="state.data.picking"
                    :options="operation_options()"
                    :card_color="utils.colors.color_for('screen_step_done')"
                    :key="make_state_component_key(['reception-picking-item-detail', state.data.picking.id])"
                />
            </template>
            <template v-if="state_is('select_document')">
                <manual-select
                    class="with-progress-bar"
                    :records="state.data.pickings"
                    :options="manual_select_options_for_select_document(true)"
                    :key="make_state_component_key(['reception', 'manual-select-document'])"
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
            </template>
            <template v-if="state_is('manual_selection') && visible_pickings">
                <list-filter
                    v-on:found="on_search"
                    :input_placeholder="filter_input_placeholder"
                />
                <manual-select
                    class="with-progress-bar"
                    :records="visible_pickings"
                    :options="manual_select_options_for_select_document()"
                    :key="make_state_component_key(['reception', 'manual-select-document'])"
                />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-back />
                        </v-col>
                    </v-row>
                </div>
            </template>
            <template v-if="state_is('select_move')">
                <manual-select
                    :card_color="utils.colors.color_for('screen_step_done')"
                    :records="ordered_moves"
                    :options="picking_detail_options_for_select_move()"
                    :key="make_state_component_key(['reception', 'manual-select-move'])"
                 />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-action @click="state.on_mark_as_done">Mark as Done</btn-action>
                        </v-col>
                    </v-row>
                </div>
            </template>
            <template v-if="state_is('confirm_done')">
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
            </template>
            <template v-if="state_is('set_lot')">
                <item-detail-card
                    :record="line_being_handled"
                    :options="picking_detail_options_for_set_lot()"
                    :card_color="lot_has_expiry_date() ? utils.colors.color_for('screen_step_done') : utils.colors.color_for('screen_step_todo')"
                    :key="make_state_component_key(['reception-product-item-detail-set-lot', state.data.picking.id])"
                />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-action @click="state.on_confirm_action">Continue</btn-action>
                        </v-col>
                    </v-row>
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-back/>
                        </v-col>
                    </v-row>
                </div>
            </template>
            <template v-if="state_is('set_quantity')">
                <item-detail-card
                    :record="line_being_handled"
                    :options="picking_detail_options_for_set_quantity()"
                    :card_color="utils.colors.color_for('screen_step_done')"
                    :key="make_state_component_key(['reception-product-item-detail-set-quantity', state.data.picking.id])"
                />
                <v-card class="pa-2" :color="utils.colors.color_for('screen_step_todo')">
                    <packaging-qty-picker
                        :key="make_state_component_key(['packaging-qty-picker', line_being_handled.id])"
                        v-bind="utils.wms.move_line_qty_picker_props(line_being_handled)"
                        :card_color="utils.colors.color_for('screen_step_todo')"
                    />
                </v-card>
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-action @click="state.on_add_to_existing_pack">Existing pack</btn-action>
                        </v-col>
                    </v-row>
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-action @click="state.on_create_new_pack">New pack</btn-action>
                        </v-col>
                    </v-row>
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-action @click="state.on_process_without_pack">Process without pack</btn-action>
                        </v-col>
                    </v-row>
                    <div class="button-list button-vertical-list full">
                        <v-row align="center">
                            <v-col class="text-center" cols="12">
                                <btn-back/>
                            </v-col>
                            <v-col class="text-center" cols="12">
                                <cancel-button/>
                            </v-col>
                        </v-row>
                    </div>
                </div>
            </template>
            <template v-if="state_is('set_destination')">
                <item-detail-card
                    :record="line_being_handled"
                    :options="picking_detail_options_for_set_destination()"
                    :card_color="utils.colors.color_for('screen_step_done')"
                    :key="make_state_component_key(['reception-product-item-detail-set-destination-pack', state.data.picking.id])"
                />
                <item-detail-card
                    :record="line_being_handled"
                    :card_color="utils.colors.color_for('screen_step_todo')"
                    :options="{key_title: 'location_dest.name'}"
                    :key="make_state_component_key(['reception-product-item-detail-set-destination-dest-location', state.data.picking.id])"
                />
            </template>
            <template v-if="state_is('select_dest_package')">
                <item-detail-card
                    v-if="state.data.picking.note"
                    :record="state.data.picking"
                    :options="picking_detail_options_for_select_dest_package()"
                    :card_color="utils.colors.color_for('screen_step_done')"
                    :key="make_state_component_key(['reception-picking-item-detail', state.data.picking.id])"
                />
                <manual-select
                    :records="state.data.packages"
                    :options="manual_select_options_for_select_dest_package()"
                    :key="make_state_component_key(['reception', 'manual-select-dest-package'])"
                />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-back/>
                        </v-col>
                    </v-row>
                </div>
            </template>
            <template v-if="state_is('confirm_new_package')">
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
            </template>
        </Screen>
    `,
    computed: {
        visible_pickings: function () {
            return !_.isEmpty(this.filtered_pickings)
                ? this.filtered_pickings
                : this.state.data.pickings;
        },
        search_input_placeholder_expiry: function () {
            return this.state.display_info.scan_input_placeholder_expiry;
        },
        line_being_handled: function () {
            return this.state.data.selected_move_line[0] || {};
        },
        ordered_moves: function () {
            const moves = _.result(this.state, "data.picking.moves", []);
            if (_.isEmpty(moves)) {
                return;
            }
            // We sort the moves to ensure that the following order always takes place:
            // Top: Partially done moves.
            // Middle: Moves with 0 quantity_done.
            // Bottom: Completely done moves.
            return moves.sort((a, b) => a.progress - b.progress);
        },
    },
    methods: {
        screen_title: function () {
            if (_.isEmpty(this.current_doc()) || this.state_is("select_document")) {
                return this.menu_item().name;
            }
            const title = this.current_doc().record.name;
            return title;
        },
        current_doc: function () {
            const data = this.state_get_data("select_move");
            if (_.isEmpty(data)) {
                return null;
            }
            return {
                record: data.picking,
                identifier: data.picking.name,
            };
        },
        picking_display_fields: function () {
            return [
                {path: "origin", label: "Source Document"},
                {path: "partner.name", label: "Partner"},
                {path: "carrier"},
                {
                    path: "scheduled_date",
                    renderer: (rec, field) => {
                        return (
                            "Scheduled Date: " +
                            this.utils.display.render_field_date(rec, field)
                        );
                    },
                },
            ];
        },
        operation_options: function () {
            return {
                title_action_field: {action_val_path: "name"},
                fields: this.picking_display_fields(),
            };
        },
        select_document_display_fields: function () {
            var fields = this.picking_display_fields();
            fields.push({path: "move_line_count", label: "Lines"});
            return fields;
        },
        manual_select_options_for_select_document: function (today_only = false) {
            return {
                group_title_default: today_only
                    ? "Pickings to process today"
                    : "Pickings to process",
                group_color: this.utils.colors.color_for("screen_step_todo"),
                list_item_extra_component: "picking-list-item-progress-bar",
                showActions: false,
                list_item_options: {
                    key_title: "name",
                    loud_title: true,
                    title_action_field: {
                        action_val_path: "name",
                    },
                    fields: this.select_document_display_fields(),
                },
            };
        },
        picking_detail_options_for_set_lot: function () {
            return {
                key_title: "product.display_name",
                fields: [
                    {
                        path: "product.supplier_code",
                        label: "Vendor code",
                    },
                    {
                        path: "product.barcode",
                        label: "Barcode",
                    },
                    {path: "lot.name", label: "Lot", klass: "loud"},
                    {
                        path: "lot.expiration_date",
                        label: "Expiry date",
                        klass: "loud",
                        renderer: (rec, field) => {
                            return this.utils.display.render_field_date(rec, field);
                        },
                    },
                ],
            };
        },
        picking_detail_options_for_set_quantity: function () {
            return {
                key_title: "product.display_name",
                fields: [
                    {
                        path: "product.barcode",
                        label: "Barcode",
                    },
                    {
                        path: "product.supplier_code",
                        label: "Vendor code",
                    },
                    {path: "lot.name", label: "Lot"},
                    {
                        path: "lot.expiration_date",
                        label: "Expiry date",
                        renderer: (rec, field) => {
                            return this.utils.display.render_field_date(rec, field);
                        },
                    },
                ],
            };
        },
        picking_detail_options_for_select_move: function (move) {
            return {
                show_title: true,
                showActions: false,
                list_item_options: {
                    loud_title: true,
                    title_action_field: {
                        action_val_path: "name",
                    },
                    list_item_klass_maker: this.move_card_color,
                    key_title: "product.display_name",
                    fields: [
                        {
                            path: "product.barcode",
                            label: "Barcode",
                        },
                        {
                            path: "product.supplier_code",
                            label: "Vendor code",
                        },
                        {
                            path: "quantity_done",
                            label: "Qty done",
                            display_no_value: true,
                        },
                    ],
                },
            };
        },
        picking_detail_options_for_set_destination: function () {
            return {
                key_title: "product.display_name",
                fields: [
                    {
                        path: "product.supplier_code",
                        label: "Vendor code",
                    },
                    {
                        path: "product.barcode",
                        label: "Barcode",
                        action_val_path: "barcode",
                    },
                    {
                        path: "lot.name",
                        label: "Lot",
                    },
                    {
                        path: "lot.expiration_date",
                        label: "Expiry date",
                        renderer: (rec, field) => {
                            return this.utils.display.render_field_date(rec, field);
                        },
                    },
                    {
                        path: "package_dest.name",
                        label: "Pack",
                        klass: "loud",
                    },
                ],
            };
        },
        select_dest_package_display_name_values: function (rec) {
            var values = [];
            if (rec.origin) {
                values.push(rec.origin);
            }
            if (rec.partner.name) {
                values.push(rec.partner.name);
            }
            return values;
        },
        select_dest_package_display_name: function (rec) {
            var values = this.select_dest_package_display_name_values();
            return values.join(" - ");
        },
        picking_detail_options_for_select_dest_package: function () {
            return {
                fields: [
                    {
                        path: "origin",
                        renderer: (rec, field) => {
                            return this.select_dest_package_display_name(rec);
                        },
                    },
                ],
            };
        },
        manual_select_options_for_select_dest_package: function () {
            return {
                group_title_default: "Packs available",
                group_color: this.utils.colors.color_for("screen_step_todo"),
                list_item_component: "list-item",
                list_item_options: {
                    fields: [
                        {path: "weight", label: "Weight", display_no_value: true},
                        {
                            path: "move_line_count",
                            label: "Lines already in pack",
                            display_no_value: true,
                        },
                        {path: "storage_type.name", label: "Package type"},
                    ],
                },
            };
        },
        on_search: function (input) {
            this.filtered_pickings = this.state.data.pickings.filter((picking) =>
                this._apply_search_filter(picking, input.text)
            );
        },
        reset_picking_filter: function () {
            this.filtered_pickings = [];
        },
        lot_has_expiry_date: function () {
            // If there's a expiry date, it means there's a lot too.
            const expiry_date = _.result(
                this.line_being_handled,
                "lot.expiration_date",
                ""
            );
            return !_.isEmpty(expiry_date);
        },
        get_expiration_date_from_lot: function (lot) {
            if (!lot.expiration_date) {
                return;
            }
            return lot.expiration_date.split("T")[0];
        },
        move_card_color: function (move) {
            if (move.progress === 100) {
                return "screen_step_done";
            } else {
                return "screen_step_todo";
            }
        },
        _apply_search_filter: function (picking, input) {
            if (_.isEmpty(picking.origin)) {
                return false;
            }
            return picking.origin.includes(input);
        },
        _get_states: function () {
            return reception_states.bind(this)();
        },
    },
    data: function () {
        return {
            usage: "reception",
            initial_state_key: "select_document",
            scan_destination_qty: 0,
            states: this._get_states(),
            filter_input_placeholder: "Find an operation",
            filtered_pickings: [],
        };
    },
};

process_registry.add("reception", Reception);

export default Reception;
