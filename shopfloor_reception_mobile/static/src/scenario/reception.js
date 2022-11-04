/**
 * Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
 */

import {ScenarioBaseMixin} from "/shopfloor_mobile_base/static/wms/src/scenario/mixins.js";
import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

const Reception = {
    mixins: [ScenarioBaseMixin],
    template: `
        <Screen :screen_info="screen_info">
            <template v-slot:header>
                <state-display-info :info="state.display_info" v-if="state.display_info"/>
            </template>
            <searchbar
                v-if="state_in(['select_document', 'select_line', 'set_lot', 'set_quantity', 'set_destination', 'select_dest_package'])"
                v-on:found="on_scan"
                :input_placeholder="search_input_placeholder"
            />
            <date-picker-input v-if="state_is('set_lot')"/>
            <template v-if="state_in(['select_line', 'set_lot', 'set_quantity', 'set_destination'])">
                <item-detail-card
                    :record="state.data.picking"
                    :options="operation_options()"
                    :card_color="utils.colors.color_for('screen_step_done')"
                    :key="make_state_component_key(['reception-picking-item-detail', state.data.picking.id])"
                />
            </template>
            <template v-if="state_is('select_document') && visible_pickings">
                <searchbar
                    v-on:found="on_search"
                    :input_placeholder="filter_input_placeholder"
                    :autofocus="false"
                    clearable_input_type
                />
                <manual-select
                    class="with-progress-bar"
                    :records="visible_pickings"
                    :options="manual_select_options_for_select_document()"
                    v-on:select="on_select_document"
                    :key="make_state_component_key(['reception', 'manual-select-document'])"
                />
            </template>
            <template v-if="state_is('select_line')">
                <picking-summary
                    :record="state.data.picking"
                    :records_grouped="picking_summary_records_grouped(state.data.picking)"
                    :action_cancel_package_key="'package_dest'"
                    :list_options="picking_summary_options_for_select_line()"
                    :key="make_state_component_key(['picking-summary', 'detail-picking', state.data.picking.id])"
                />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-action @click="on_mark_done">Mark as Done</btn-action>
                        </v-col>
                    </v-row>
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-back />
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
                    :record="state.data"
                    :options="picking_detail_options_for_set_lot()"
                    :card_color="utils.colors.color_for('screen_step_todo')"
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
                    :record="state.data"
                    :options="picking_detail_options_for_set_quantity()"
                    :card_color="utils.colors.color_for('screen_step_done')"
                    :key="make_state_component_key(['reception-product-item-detail-set-quantity', state.data.picking.id])"
                />
                <v-card class="pa-2" :color="utils.colors.color_for('screen_step_todo')">
                    <packaging-qty-picker
                        :key="make_state_component_key(['packaging-qty-picker', get_line_being_handled().id])"
                        :options="utils.wms.move_line_qty_picker_options(get_line_being_handled())"
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
                </div>
            </template>
            <template v-if="state_is('set_destination')">
                <item-detail-card
                    :record="state.data"
                    :options="picking_detail_options_for_set_destination()"
                    :card_color="utils.colors.color_for('screen_step_todo')"
                    :key="make_state_component_key(['reception-product-item-detail-set-destination-pack', state.data.picking.id])"
                />
                <item-detail-card
                    :record="state.data"
                    :card_color="utils.colors.color_for('screen_step_todo')"
                    :options="{key_title: 'selected_move_lines[0].location_dest.barcode'}"
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
            const data = this.state_get_data("select_line");
            if (_.isEmpty(data)) {
                return null;
            }
            return {
                record: data.picking,
                identifier: data.picking.name,
            };
        },
        manual_select_options_for_select_document: function () {
            return {
                group_title_default: "Pickings to process",
                group_color: this.utils.colors.color_for("screen_step_todo"),
                list_item_extra_component: "picking-list-item-progress-bar",
                showActions: false,
                list_item_options: {
                    key_title: "name",
                    loud_title: true,
                    fields: [
                        {path: "origin", action_val_path: "name"},
                        {path: "carrier"},
                        {
                            path: "scheduled_date",
                            renderer: (rec, field) => {
                                return this.utils.display.render_field_date(rec, field);
                            },
                        },
                        {path: "move_line_count", label: "Lines"},
                    ],
                },
            };
        },
        operation_options: function () {
            return {
                title_action_field: {action_val_path: "name"},
                fields: [
                    {
                        path: "origin",
                        renderer: (rec, field) => {
                            return rec.origin + " - " + rec.partner.name;
                        },
                    },
                    {path: "carrier"},
                ],
            };
        },
        picking_detail_options_for_set_lot: function () {
            return {
                key_title: "selected_move_lines[0].product.display_name",
                fields: [
                    {
                        path: "selected_move_lines[0].product.supplier_code",
                        label: "Vendor code",
                    },
                    {
                        path: "selected_move_lines[0].product.barcode",
                        label: "Product code",
                        action_val_path: "barcode",
                    },
                    {path: "selected_move_lines[0].package_dest.name", label: "Pack"},
                    {path: "selected_move_lines[0].lot.name", label: "Lot"},
                    {
                        path: "picking.scheduled_date",
                        label: "Scheduled date",
                        renderer: (rec, field) => {
                            return this.utils.display.render_field_date(rec, field);
                        },
                    },
                ],
            };
        },
        picking_detail_options_for_set_quantity: function () {
            return {
                key_title: "selected_move_lines[0].product.display_name",
                fields: [
                    {
                        path: "selected_move_lines[0].product.supplier_code",
                        label: "Vendor code",
                    },
                    {
                        path: "selected_move_lines[0].product.barcode",
                        label: "Product code",
                        action_val_path: "barcode",
                    },
                    {path: "selected_move_lines[0].lot.name", label: "Lot"},
                    // TODO: need exp. date & remov. date from the backend
                    {
                        path: "picking.scheduled_date",
                        label: "Scheduled date",
                        renderer: (rec, field) => {
                            return this.utils.display.render_field_date(rec, field);
                        },
                    },
                ],
            };
        },
        picking_summary_options_for_select_line: function () {
            return {
                show_title: false,
                list_item_options: {
                    // TODO: uncomment this line once the backend has an endpoint to cancel lines.
                    // actions: ["action_cancel_line"],
                    fields: [
                        {path: "product.barcode", label: "Product code"},
                        {path: "product.supplier_code", label: "Vendor code"},
                        {path: "package_dest.name", label: "Pack"},
                        {
                            path: "qty_done",
                            label: "Received qty",
                            display_no_value: true,
                            renderer: (rec, field) => {
                                return rec.qty_done ? rec.qty_done : "None";
                            },
                        },
                    ],
                    header_fields: [{path: "product.barcode", label: "Product code"}],
                    group_header_title_key: "display_name",
                    list_item_klass_maker: this.utils.wms.move_line_color_klass,
                },
            };
        },
        picking_detail_options_for_set_destination: function () {
            return {
                key_title: "selected_move_lines[0].product.display_name",
                fields: [
                    {
                        path: "selected_move_lines[0].product.supplier_code",
                        label: "Vendor code",
                    },
                    {
                        path: "selected_move_lines[0].product.barcode",
                        label: "Product code",
                        action_val_path: "barcode",
                    },
                    {
                        path: "picking.scheduled_date",
                        label: "Scheduled date",
                        renderer: (rec, field) => {
                            return this.utils.display.render_field_date(rec, field);
                        },
                    },
                    {path: "selected_move_lines[0].package_dest.name", label: "Pack"},
                ],
            };
        },
        picking_detail_options_for_select_dest_package: function () {
            return {
                fields: [
                    {
                        path: "origin",
                        renderer: (rec, field) => {
                            return rec.origin + " - " + rec.partner.name;
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
                    fields: [{path: "weight", label: "Weight"}],
                },
            };
        },
        picking_summary_records_grouped: function (picking) {
            return this.utils.wms.group_lines_by_product(picking.move_lines, {
                prepare_records: _.partialRight(
                    this.utils.wms.group_by_pack,
                    "product"
                ),
                group_color_maker: function (lines) {
                    return picking.completion == 100
                        ? "screen_step_done"
                        : "screen_step_todo";
                },
                group_no_title: true,
            });
        },
        on_search: function (input) {
            this.filtered_pickings = this.state.data.pickings.filter((picking) =>
                this._apply_search_filter(picking, input.text)
            );
        },
        on_select_document: function (selected) {
            this.$root.trigger("scan", selected.name);
        },
        on_mark_done: function () {
            this.$root.trigger("mark_as_done");
        },
        get_line_being_handled: function () {
            return this.state.data.selected_move_lines[0];
        },
        get_next_line_id_to_handle: function () {
            // The enpoints in the backend accept multiple selected line ids.
            // However, in this particular scenario, we only want to deal with one line at a time.
            // For that, we select the first line we find that hasn't been completely dealt with yet.
            const next_unhandled_line = this.state.data.selected_move_lines.find(
                (line) => line.qty_done < line.quantity
            );
            return this._get_selected_line_ids([next_unhandled_line]);
        },
        _apply_search_filter: function (picking, input) {
            const values = [picking.origin];
            return !_.isEmpty(values.find((v) => v.includes(input)));
        },
        _get_selected_line_ids: function (lines) {
            return lines.map(_.property("id"));
        },
    },
    data: function () {
        return {
            usage: "reception",
            initial_state_key: "select_document",
            scan_destination_qty: 0,
            states: {
                init: {
                    enter: () => {
                        this.wait_call(this.odoo.call("start"));
                    },
                },
                select_document: {
                    display_info: {
                        title: "Choose an operation",
                        scan_placeholder: "Scan document / product / package",
                    },
                    events: {
                        select: "on_select",
                    },
                    on_select: (selected) => {
                        this.wait_call(
                            this.odoo.call("scan_document", {
                                barcode: selected.name,
                            })
                        );
                    },
                    on_scan: (barcode) => {
                        this.wait_call(
                            this.odoo.call("scan_document", {
                                barcode: barcode.text,
                            })
                        );
                    },
                },
                select_line: {
                    display_info: {
                        title: "Select a line",
                        scan_placeholder: "Scan product / package",
                    },
                    events: {
                        mark_as_done: "on_mark_as_done",
                        cancel_picking_line: "on_cancel",
                    },
                    on_scan: (barcode) => {
                        this.wait_call(
                            this.odoo.call("scan_line", {
                                picking_id: this.state.data.picking.id,
                                barcode: barcode.text,
                            })
                        );
                    },
                    on_mark_as_done: () => {
                        this.wait_call(
                            this.odoo.call("done_action", {
                                picking_id: this.state.data.picking.id,
                            })
                        );
                    },
                    on_cancel: () => {
                        // TODO: endpoint missing in backend
                        // this.wait_call(
                        //     this.odoo.call("cancel", {
                        //         package_level_id: this.state.data.id,
                        //     })
                        // );
                    },
                },
                confirm_done: {
                    display_info: {
                        title: "Confirm done",
                    },
                    events: {
                        confirm: "on_confirm",
                    },
                    on_confirm: () => {
                        this.wait_call(
                            this.odoo.call("done_action", {
                                picking_id: this.state.data.picking.id,
                                confirmation: true,
                            })
                        );
                    },
                    on_back: () => {
                        this.state_to("select_line");
                        this.reset_notification();
                    },
                },
                set_lot: {
                    display_info: {
                        title: "Set lot",
                        scan_placeholder: "Scan lot",
                        scan_input_placeholder_expiry: "Scan expiration date",
                    },
                    events: {
                        date_picker_selected: "on_date_picker_selected",
                    },
                    // NOTE: in these three calls, selected_line_ids will consist of just
                    // one id (the next one to be handled).
                    on_scan: (barcode) => {
                        this.wait_call(
                            this.odoo.call("set_lot", {
                                picking_id: this.state.data.picking.id,
                                selected_line_ids: this.get_next_line_id_to_handle(),
                                lot_name: barcode.text,
                            })
                        );
                    },
                    on_date_picker_selected: (expiration_date) => {
                        this.wait_call(
                            this.odoo.call("set_lot", {
                                picking_id: this.state.data.picking.id,
                                selected_line_ids: this.get_next_line_id_to_handle(),
                                expiration_date: expiration_date,
                            })
                        );
                    },
                    on_confirm_action: () => {
                        this.wait_call(
                            this.odoo.call("set_lot_confirm_action", {
                                picking_id: this.state.data.picking.id,
                                selected_line_ids: this.get_next_line_id_to_handle(),
                            })
                        );
                    },
                },
                set_quantity: {
                    display_info: {
                        title: "Set quantity",
                        scan_placeholder:
                            "Scan document / product / package / location",
                    },
                    events: {
                        qty_edit: "on_qty_edit",
                    },
                    on_qty_edit: (qty) => {
                        this.scan_destination_qty = parseInt(qty, 10);
                    },
                    on_scan: (barcode) => {
                        this.wait_call(
                            this.odoo.call("set_quantity", {
                                // TODO: add quantity from qty-picker
                                picking_id: this.state.data.picking.id,
                                selected_line_ids: this._get_selected_line_ids(
                                    this.state.data.selected_move_lines
                                ),
                                quantity: this.scan_destination_qty,
                                barcode,
                                confirmation: true,
                            })
                        );
                    },
                    on_cancel: () => {
                        // TODO: endpoint missing in backend
                        // this.wait_call(
                        //     this.odoo.call("cancel", {
                        //         package_level_id: this.state.data.id,
                        //     })
                        // );
                    },
                    on_add_to_existing_pack: () => {
                        this.wait_call(
                            this.odoo.call("process_with_existing_pack", {
                                picking_id: this.state.data.picking.id,
                                selected_line_ids: this._get_selected_line_ids(
                                    this.state.data.selected_move_lines
                                ),
                                quantity: this.scan_destination_qty,
                            })
                        );
                    },
                    on_create_new_pack: () => {
                        this.wait_call(
                            this.odoo.call("process_with_new_pack", {
                                picking_id: this.state.data.picking.id,
                                selected_line_ids: this._get_selected_line_ids(
                                    this.state.data.selected_move_lines
                                ),
                                quantity: this.scan_destination_qty,
                            })
                        );
                    },
                    on_process_without_pack: () => {
                        this.wait_call(
                            this.odoo.call("process_without_pack", {
                                picking_id: this.state.data.picking.id,
                                selected_line_ids: this._get_selected_line_ids(
                                    this.state.data.selected_move_lines
                                ),
                                quantity: this.scan_destination_qty,
                            })
                        );
                    },
                },
                set_destination: {
                    display_info: {
                        title: "Set destination",
                        scan_placeholder: "Scan destination location",
                    },
                    on_scan: (location) => {
                        this.wait_call(
                            this.odoo.call("set_destination", {
                                picking_id: this.state.data.picking.id,
                                selected_line_ids: this._get_selected_line_ids(
                                    this.state.data.selected_move_lines
                                ),
                                location_id: location.text,
                                confirmation: true,
                            })
                        );
                    },
                },
                select_dest_package: {
                    display_info: {
                        title: "Select destination package",
                        scan_placeholder: "Scan destination package",
                    },
                    events: {
                        select: "on_select",
                    },
                    on_scan: (barcode) => {
                        this.wait_call(
                            this.odoo.call("select_dest_package", {
                                picking_id: this.state.data.picking.id,
                                selected_line_ids: this._get_selected_line_ids(
                                    this.state.data.selected_move_lines
                                ),
                                barcode,
                            })
                        );
                    },
                },
            },
            filter_input_placeholder: "Filter operations",
            filtered_pickings: [],
        };
    },
};

process_registry.add("reception", Reception);

export default Reception;

// TODO: handle all confirmations in the scenario
