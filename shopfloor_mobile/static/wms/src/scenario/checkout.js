/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ScenarioBaseMixin} from "/shopfloor_mobile_base/static/wms/src/scenario/mixins.js";
import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

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
                v-if="state.on_scan"
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
                    :record="state.data.picking"
                    :select_records="state.data.picking.move_lines"
                    :select_records_grouped="utils.wms.group_lines_by_location(state.data.picking.move_lines, {'prepare_records': utils.wms.only_one_package})"
                    :select_options="select_line_manual_select_opts()"
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
                <v-alert type="info" tile v-if="state.data.packing_info" class="packing-info">
                    <p v-text="state.data.packing_info" />
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
                                   :disabled="_.isEmpty(selected_lines()) || _.isEmpty(state.data.picking.carrier)"
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
                        :options="utils.wms.move_line_qty_picker_options(state.data.line)"
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
        </Screen>
        `,
    computed: {
        existing_package_select_fields: function() {
            return [
                {path: "weight"},
                {path: "move_line_count", label: "Line count"},
                {path: "packaging.name"},
            ];
        },
    },
    methods: {
        current_carrier: function() {
            return (
                this.state.data.picking.carrier || this.state.data.picking.ship_carrier
            );
        },
        screen_title: function() {
            if (_.isEmpty(this.current_doc()) || this.state_is("confirm_start"))
                return this.menu_item().name;
            let title = this.current_doc().record.name;
            return title;
        },
        current_doc: function() {
            const data = this.state_get_data("select_line");
            if (_.isEmpty(data)) {
                return null;
            }
            return {
                record: data.picking,
                identifier: data.picking.name,
            };
        },
        manual_selection_manual_select_options: function() {
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
                    ],
                },
            };
        },
        select_delivery_packaging_manual_select_options: function() {
            return {
                showActions: false,
                list_item_options: {
                    loud_title: true,
                    fields: [{path: "packaging_type"}],
                },
            };
        },
        select_line_manual_select_opts: function() {
            return {
                group_color: this.utils.colors.color_for("screen_step_todo"),
                card_klass: "loud-labels",
            };
        },
        select_package_manual_select_opts: function() {
            return {
                multiple: true,
                initValue: this.selected_line_ids(),
                card_klass: "loud-labels",
                list_item_component: "picking-select-package-content",
                list_item_options: {actions: ["action_qty_edit"]},
            };
        },
        selectable_lines: function() {
            const stored = this.state_get_data("select_package");
            return _.result(stored, "selected_move_lines", []);
        },
        selectable_line_ids: function() {
            return this.selectable_lines().map(_.property("id"));
        },
        selected_lines: function() {
            return this.selectable_lines().filter(function(x) {
                return x.qty_done > 0;
            });
        },
        selected_line_ids: function() {
            return this.selected_lines().map(_.property("id"));
        },
    },
    data: function() {
        return {
            usage: "checkout",
            initial_state_key: "select_document",
            states: {
                select_document: {
                    display_info: {
                        title: "Choose an order to pack",
                        scan_placeholder: "Scan pack / picking / location",
                    },
                    on_scan: scanned => {
                        this.wait_call(
                            this.odoo.call("scan_document", {barcode: scanned.text})
                        );
                    },
                    on_manual_selection: evt => {
                        this.wait_call(this.odoo.call("list_stock_picking"));
                    },
                },
                manual_selection: {
                    display_info: {
                        title: "Select a picking and start",
                    },
                    events: {
                        select: "on_select",
                        go_back: "on_back",
                    },
                    on_back: () => {
                        this.state_to("init");
                        this.reset_notification();
                    },
                    on_select: selected => {
                        this.wait_call(
                            this.odoo.call("select", {
                                picking_id: selected.id,
                            })
                        );
                    },
                },
                select_line: {
                    display_info: {
                        title: "Pick the product by scanning something",
                        scan_placeholder: "Scan pack / product / lot",
                    },
                    events: {
                        summary: "on_summary",
                        select: "on_select",
                        back: "on_back",
                    },
                    on_scan: scanned => {
                        this.wait_call(
                            this.odoo.call("scan_line", {
                                picking_id: this.state.data.picking.id,
                                barcode: scanned.text,
                            })
                        );
                    },
                    on_select: selected => {
                        if (!selected) {
                            return;
                        }
                        this.wait_call(
                            this.odoo.call("select_line", {
                                picking_id: this.state.data.picking.id,
                                move_line_id: selected.id,
                                package_id: _.result(
                                    selected,
                                    "package_dest.id",
                                    false
                                ),
                            })
                        );
                    },
                    on_back: () => {
                        this.state_to("start");
                        this.reset_notification();
                    },
                    on_summary: () => {
                        this.wait_call(
                            this.odoo.call("summary", {
                                picking_id: this.state.data.picking.id,
                            })
                        );
                    },
                    // FIXME: is not to change qty
                    on_edit_package: pkg => {
                        this.state_set_data({package: pkg}, change_quantity);
                        this.state_to("change_quantity");
                    },
                },
                select_package: {
                    // TODO: /set_line_qty is not handled yet
                    // because is not clear how to handle line selection
                    // and qty set.
                    // ATM given that manual-select uses v-list-item-group
                    // when you touch a line you select/unselect it
                    // which means we cannot rely on this to go to edit.
                    // If we need it, we have to change manual-select
                    // to use pure list + checkboxes.
                    display_info: {
                        title: "Select package",
                        scan_placeholder: "Scan existing package / package type",
                    },
                    events: {
                        qty_edit: "on_qty_edit",
                        select: "on_select",
                        back: "on_back",
                    },
                    on_scan: scanned => {
                        this.wait_call(
                            this.odoo.call("scan_package_action", {
                                picking_id: this.state.data.picking.id,
                                selected_line_ids: this.selectable_line_ids(),
                                barcode: scanned.text,
                            })
                        );
                    },
                    on_select: selected => {
                        if (!selected) {
                            return;
                        }
                        const orig_selected = this.selected_line_ids();
                        const selected_ids = selected.map(_.property("id"));
                        const to_select = _.head(
                            this.selectable_lines().filter(function(x) {
                                return (
                                    selected_ids.includes(x.id) &&
                                    !orig_selected.includes(x.id)
                                );
                            })
                        );
                        const to_unselect = _.head(
                            this.selectable_lines().filter(function(x) {
                                return (
                                    !selected_ids.includes(x.id) &&
                                    orig_selected.includes(x.id)
                                );
                            })
                        );
                        let endpoint, move_line;
                        if (to_unselect) {
                            endpoint = "reset_line_qty";
                            move_line = to_unselect;
                        } else if (to_select) {
                            endpoint = "set_line_qty";
                            move_line = to_select;
                        }
                        this.wait_call(
                            this.odoo.call(endpoint, {
                                picking_id: this.state.data.picking.id,
                                selected_line_ids: this.selectable_line_ids(),
                                move_line_id: move_line.id,
                            })
                        );
                    },
                    on_qty_edit: record => {
                        this.state_set_data(
                            {
                                picking: this.state.data.picking,
                                line: record,
                                selected_line_ids: this.selectable_line_ids(),
                            },
                            "change_quantity"
                        );
                        this.state_to("change_quantity");
                    },
                    on_new_pack: () => {
                        this.wait_call(
                            this.odoo.call("list_delivery_packaging", {
                                picking_id: this.state.data.picking.id,
                                selected_line_ids: this.selectable_line_ids(),
                            })
                        );
                    },
                    on_existing_pack: () => {
                        this.wait_call(
                            this.odoo.call("list_dest_package", {
                                picking_id: this.state.data.picking.id,
                                selected_line_ids: this.selectable_line_ids(),
                            })
                        );
                    },
                    on_without_pack: () => {
                        this.wait_call(
                            this.odoo.call("no_package", {
                                picking_id: this.state.data.picking.id,
                                selected_line_ids: this.selectable_line_ids(),
                            })
                        );
                    },
                    on_back: () => {
                        this.state_to("select_line");
                        this.reset_notification();
                    },
                },
                select_delivery_packaging: {
                    display_info: {
                        title: "Select delivery packaging",
                        scan_placeholder: "Scan package type",
                    },
                    events: {
                        select: "on_select",
                        back: "on_back",
                    },
                    on_select: selected => {
                        this.state.on_scan({text: selected.barcode});
                    },
                    on_scan: scanned => {
                        const picking = this.current_doc().record;
                        this.wait_call(
                            this.odoo.call("scan_package_action", {
                                picking_id: picking.id,
                                selected_line_ids: this.selected_line_ids(),
                                barcode: scanned.text,
                            })
                        );
                    },
                },
                change_quantity: {
                    display_info: {
                        title: "Change quantity",
                    },
                    events: {
                        qty_change_confirm: "on_confirm",
                        qty_edit: "on_qty_update",
                    },
                    on_back: () => {
                        this.state_to("select_package");
                        this.reset_notification();
                    },
                    on_qty_update: qty => {
                        this.state.data.qty = qty;
                    },
                    on_confirm: () => {
                        this.wait_call(
                            this.odoo.call("set_custom_qty", {
                                picking_id: this.state.data.picking.id,
                                selected_line_ids: this.selected_line_ids(),
                                move_line_id: this.state.data.line.id,
                                qty_done: this.state.data.qty,
                            })
                        );
                    },
                },
                select_dest_package: {
                    display_info: {
                        title: "Select destination package",
                    },
                    events: {
                        select: "on_select",
                        back: "on_back",
                    },
                    on_scan: scanned => {
                        this.wait_call(
                            this.odoo.call("scan_dest_package", {
                                picking_id: this.state.data.picking.id,
                                selected_line_ids: this.selected_line_ids(),
                                barcode: scanned.text,
                            })
                        );
                    },
                    on_select: selected => {
                        if (!selected) {
                            return;
                        }
                        this.wait_call(
                            this.odoo.call("set_dest_package", {
                                picking_id: this.state.data.picking.id,
                                selected_line_ids: this.selected_line_ids(),
                                package_id: selected.id,
                            })
                        );
                    },
                    on_back: () => {
                        this.state_to("select_package");
                        this.reset_notification();
                    },
                },
                summary: {
                    display_info: {
                        title: "Summary",
                    },
                    events: {
                        select: "on_select",
                        back: "on_back",
                        cancel_picking_line: "on_cancel",
                        pkg_change_type: "on_pkg_change_type",
                        mark_as_done: "on_mark_as_done",
                        continue: "on_continue",
                    },
                    on_back: () => {
                        this.state_to("start");
                        this.reset_notification();
                    },
                    on_pkg_change_type: pkg => {
                        this.wait_call(
                            this.odoo.call("list_packaging", {
                                picking_id: this.state.data.picking.id,
                                package_id: pkg.id,
                            })
                        );
                    },
                    on_cancel: data => {
                        this.wait_call(
                            this.odoo.call("cancel_line", {
                                picking_id: this.state.data.picking.id,
                                // we get either line_id or package_id
                                package_id: data.package_id,
                                line_id: data.line_id,
                            })
                        );
                    },
                    on_mark_as_done: () => {
                        this.wait_call(
                            this.odoo.call("done", {
                                picking_id: this.state.data.picking.id,
                            })
                        );
                    },
                    on_continue: () => {
                        this.wait_call(
                            this.odoo.call("select", {
                                picking_id: this.state.data.picking.id,
                            })
                        );
                    },
                },
                change_packaging: {
                    display_info: {
                        title: "Change packaging",
                    },
                    events: {
                        select: "on_select",
                    },
                    on_select: selected => {
                        if (!selected) {
                            return;
                        }
                        this.wait_call(
                            this.odoo.call("set_packaging", {
                                picking_id: this.state.data.picking.id,
                                package_id: this.state.data.package.id,
                                packaging_id: selected.id,
                            })
                        );
                    },
                },
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
                                picking_id: this.state.data.picking.id,
                                confirmation: true,
                            })
                        );
                    },
                    on_back: () => {
                        this.state_to("summary");
                        this.reset_notification();
                    },
                },
            },
        };
    },
};

process_registry.add("checkout", Checkout);

export default Checkout;
