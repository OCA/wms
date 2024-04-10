/**
 * Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ScenarioBaseMixin} from "/shopfloor_mobile_base/static/wms/src/scenario/mixins.js";
import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

const ManualProductTransfer = {
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

            <item-detail-card
                v-if="state_in(['scan_product', 'confirm_quantity', 'change_quantity', 'scan_destination_location'])"
                :key="make_state_component_key(['manual-transfer-loc-src', location_src().id])"
                :record="location_src()"
                :options="{main: true, key_title: 'name', title_action_field: {action_val_path: 'barcode'}}"
                :card_color="utils.colors.color_for('screen_step_done')"
                />

            <item-detail-card
                v-if="state_in(['confirm_quantity', 'scan_destination_location', 'change_quantity'])"
                :key="make_state_component_key(['manual-transfer-product', product().id])"
                :record="product()"
                :options="{main: true, key_title: 'name', title_action_field: {action_val_path: 'barcode'}, fields:[{path: 'name', renderer: lot_name, label: 'Lot number'}]}"
                :card_color="utils.colors.color_for('detail_main_card')"
                />

            <div v-if="state_is('change_quantity')">
                <v-card class="pa-2" :color="utils.colors.color_for('screen_step_todo')">
                    <packaging-qty-picker
                        :key="make_state_component_key(['packaging-qty-picker', product().id])"
                        v-bind="utils.wms.move_line_qty_picker_props(fake_line())"
                        />
                </v-card>

                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-action @click="state.on_qty_change_confirm">Confirm</btn-action>
                        </v-col>
                    </v-row>
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn color="default" @click="state.on_back">Back</v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>

            <div class="detail item-detail-card" v-if="state_is('confirm_quantity') && warning()">
                <v-card :color="utils.colors.color_for('warning')">
                    <v-card-title>
                        <span class="label">
                            <v-icon>mdi-alert</v-icon>{{ warning() }}
                        </span>
                    </v-card-title>
                </v-card>
            </div>

            <v-card v-if="state_is('confirm_quantity')" class="pa-2" :color="utils.colors.color_for('screen_step_todo')">
                <packaging-qty-picker
                    :key="make_state_component_key(['packaging-qty-picker', product().id])"
                    v-bind="utils.wms.move_line_qty_picker_props(fake_line())"
                    />
            </v-card>

            <div class="detail item-detail-card" v-if="state_is('scan_destination_location')">
                <v-card :color="utils.colors.color_for('screen_step_done')">
                    <packaging-qty-picker
                        :key="make_state_component_key(['packaging-qty-picker', product().id])"
                        :readonly="true"
                        v-bind="utils.wms.move_line_qty_picker_props(fake_line())"
                        />
                </v-card>
            </div>

            <item-detail-card
                v-if="state_is('scan_destination_location')"
                :key="make_state_component_key(['manual-transfer-loc-dest', location_dest().id])"
                :record="location_dest()"
                :options="{main: true, key_title: 'name', title_action_field: {action_val_path: 'barcode'}}"
                :card_color="utils.colors.color_for('screen_step_todo')"
                />

            <div class="button-list button-vertical-list full" v-if="!state_is('change_quantity')">
                <v-row align="center"  v-if="!state_is('scan_source_location')">
                    <v-col class="text-center" cols="12" v-if="state_is('confirm_quantity')">
                        <btn-action @click="state.on_confirm_qty">Confirm quantity</btn-action>
                    </v-col>
                    <v-col class="text-center" cols="12">
                        <btn-action color="default" @click="state.on_cancel">Cancel</btn-action>
                    </v-col>
                </v-row>
            </div>
        </Screen>
        `,
    methods: {
        quantity_btn_label: function () {
            const n = 200;
            return "Quantity " + this.quantity().toString();
        },
        screen_title: function () {
            if (_.isEmpty(this.state.data.picking)) {
                return this.menu_item().name;
            }
            return this.state.data.picking.name;
        },
        state_data_check: function (data) {},
        location_src: function () {
            const data = this.state.data;
            if (_.isEmpty(data)) {
                return {};
            }
            if (!_.isEmpty(data.location)) {
                return data.location;
            }
            if (!_.isEmpty(data.move_lines[0].location_src)) {
                return data.move_lines[0].location_src;
            }
            return {};
        },
        product: function () {
            const data = this.state.data;
            if (_.isEmpty(data)) {
                return {};
            }
            if (!_.isEmpty(data.product)) {
                return data.product;
            }
            if (!_.isEmpty(data.move_lines[0].product)) {
                return data.move_lines[0].product;
            }
            return {};
        },
        warning: function () {
            return _.result(this.state, "data.warning", "");
        },
        quantity: function () {
            const data = this.state.data;
            if (_.isEmpty(data)) {
                return 0;
            }
            if ("quantity" in data) return data.quantity;
            if ("move_lines" in data) {
                return data.move_lines.reduce((total, val) => total + val.quantity, 0);
            }
            return 0;
        },
        qty_done: function () {
            const data = this.state.data;
            if (_.isEmpty(data)) {
                return 0;
            }
            if ("qty_done" in data) return data.qty_done;
            if ("quantity" in data) return data.quantity;
            if ("move_lines" in data) {
                return data.move_lines.reduce((total, val) => total + val.qty_done, 0);
            }
            return 0;
        },
        lot: function () {
            const data = this.state.data;
            if (_.isEmpty(data)) {
                return {};
            }
            if (!_.isEmpty(data.lot)) {
                return data.lot;
            }
            if (_.isEmpty(data.move_lines)) {
                return {};
            }
            if (!_.isEmpty(data.move_lines[0].lot)) {
                return data.move_lines[0].lot;
            }
            return {};
        },
        lot_name: function () {
            const lot = this.lot();
            if ("name" in lot) {
                return lot.name;
            }
            return "";
        },
        fake_line: function () {
            return {
                quantity: this.quantity(),
                qty_done: this.qty_done(),
                product: this.product(),
            };
        },
        move_line_ids: function () {
            const data = this.state.data;
            if (_.isEmpty(data)) {
                return {};
            }
            if (_.isEmpty(data.move_lines)) {
                return {};
            }
            return data.move_lines.map((line) => line.id);
        },
        location_dest: function () {
            const data = this.state.data;
            if (_.isEmpty(data)) {
                return {};
            }
            if (!_.isEmpty(data.move_lines[0].location_dest)) {
                return data.move_lines[0].location_dest;
            }
            return {};
        },
    },
    data: function () {
        const self = this;
        return {
            usage: "manual_product_transfer",
            initial_state_key: "scan_source_location",
            states: {
                scan_source_location: {
                    display_info: {
                        title: "Start by scanning a location",
                        scan_placeholder: "Scan location",
                    },
                    on_scan: (scanned) => {
                        this.wait_call(
                            this.odoo.call("scan_source_location", {
                                barcode: scanned.text,
                            })
                        );
                    },
                },
                scan_product: {
                    display_info: {
                        title: "Scan a product or a lot",
                        scan_placeholder: "Scan product or lot",
                    },
                    on_scan: (scanned) => {
                        this.wait_call(
                            this.odoo.call("scan_product", {
                                barcode: scanned.text,
                                location_id: this.location_src().id,
                            })
                        );
                    },
                    on_cancel: () => {
                        this.state_to("scan_source_location");
                    },
                },
                confirm_quantity: {
                    display_info: {
                        title: "Confirm quantity",
                        scan_placeholder: "Scan again product or a lot to confirm",
                    },
                    on_scan: (scanned) => {
                        this.wait_call(
                            this.odoo.call("confirm_quantity", {
                                location_id: this.location_src().id,
                                product_id: this.product().id,
                                quantity: this.quantity(),
                                barcode: scanned.text,
                                lot_id: this.lot().id,
                                // confirm: False,
                            })
                        );
                    },
                    on_confirm_qty: () => {
                        this.wait_call(
                            this.odoo.call("confirm_quantity", {
                                location_id: this.location_src().id,
                                product_id: this.product().id,
                                quantity: this.quantity(),
                                confirm: true,
                                lot_id: this.lot().id,
                            })
                        );
                    },
                    on_cancel: () => {
                        this.state_to("scan_source_location");
                    },
                    events: {
                        qty_edit: "on_qty_update",
                    },
                    on_qty_update: (qty) => {
                        this.state.data.quantity = qty;
                    },
                },
                change_quantity: {
                    enter: () => {
                        // This is a front end state only, so use data from
                        // previous state
                        this.state_set_data(
                            this.state_get_data("confirm_quantity"),
                            "change_quantity"
                        );
                    },
                    events: {
                        qty_edit: "on_qty_update",
                    },
                    on_qty_update: (qty) => {
                        this.state.data.quantity = qty;
                    },
                    display_info: {
                        title: "Change quantity",
                        scan_placeholder: "Should not be seen",
                    },
                    on_back: () => {
                        this.state_to("confirm_quantity");
                        this.reset_notification();
                    },
                    on_qty_change_confirm: () => {
                        this.wait_call(
                            this.odoo.call("set_quantity", {
                                location_id: this.location_src().id,
                                product_id: this.product().id,
                                quantity: this.state.data.quantity,
                                lot_id: this.lot().id,
                            })
                        );
                    },
                },
                scan_destination_location: {
                    display_info: {
                        title: "Scann a destination location",
                        scan_placeholder: "Scan location",
                    },
                    on_scan: (scanned) => {
                        this.wait_call(
                            this.odoo.call("scan_destination_location", {
                                barcode: scanned.text,
                                move_line_ids: this.move_line_ids(),
                            })
                        );
                    },
                    on_cancel: () => {
                        this.wait_call(
                            this.odoo.call("cancel", {
                                move_line_ids: this.move_line_ids(),
                            })
                        );
                    },
                },
            },
        };
    },
};

process_registry.add("manual_product_transfer", ManualProductTransfer);

export default ManualProductTransfer;
