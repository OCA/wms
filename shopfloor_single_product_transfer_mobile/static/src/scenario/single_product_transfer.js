/**
 * Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
 */

import {ScenarioBaseMixin} from "/shopfloor_mobile_base/static/wms/src/scenario/mixins.js";
import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

const SingleProductTransfer = {
    mixins: [ScenarioBaseMixin],
    template: `
        <Screen :screen_info="screen_info">
            <template v-slot:header>
                <state-display-info :info="state.display_info" v-if="state.display_info"/>
            </template>
            <searchbar
                v-if="state_in(['select_location_or_package', 'select_product', 'set_quantity', 'set_location'])"
                v-on:found="on_scan"
                :input_placeholder="search_input_placeholder"
            />
            <template v-if="state_is('select_product')">
                <item-detail-card
                    v-if="get_select_product_package_or_location_data()"
                    :key="make_state_component_key(['location-or-package', get_select_product_package_or_location_data().id])"
                    :record="get_select_product_package_or_location_data()"
                    :card_color="utils.colors.color_for('screen_step_done')"
                >
                    <template v-slot:after_details v-if="display_operations_progress()">
                        <linear-progress
                            :done_qty="get_select_product_package_or_location_data().operation_progress.done"
                            :todo_qty="get_select_product_package_or_location_data().operation_progress.to_do"
                            :options="linear_progress_options_for_select_product()"
                        />
                    </template>
                </item-detail-card>
            </template>
            <template v-if="state_is('set_quantity')">
                <item-detail-card
                    :key="make_state_component_key(['location_src', state.data.move_line.location_src.id])"
                    :record="state.data.move_line.location_src"
                    :card_color="utils.colors.color_for('screen_step_done')"
                />
                <item-detail-card
                    :key="make_state_component_key(['product', state.data.move_line.product.id])"
                    :options="product_detail_options_for_set_quantity()"
                    :record="state.data.move_line"
                    :card_color="utils.colors.color_for('screen_step_done')"
                />
                <item-detail-card
                    :key="make_state_component_key(['location_dest', state.data.move_line.location_dest.id])"
                    :record="state.data.move_line.location_dest"
                    :card_color="utils.colors.color_for('screen_step_todo')"
                />
                <v-card class="pa-2" :color="utils.colors.color_for('screen_step_todo')">
                    <packaging-qty-picker
                        :key="make_state_component_key(['packaging-qty-picker', state.data.move_line.id])"
                        v-bind="utils.wms.move_line_qty_picker_props(state.data.move_line)"
                    />
                </v-card>
            </template>
            <template v-if="state_is('set_location')">
                <item-detail-card
                    :key="make_state_component_key(['move_line', state.data.move_line.id])"
                    :record="state.data.move_line"
                    :options="move_line_options_for_set_location()"
                    :card_color="utils.colors.color_for('screen_step_done')"
                />
                <item-detail-card
                    :key="make_state_component_key(['package_dest', state.data.package.id])"
                    :record="state.data.package"
                    :options="{title_action_field: {path: 'name', action_val_path: 'name'}}"
                    :card_color="utils.colors.color_for('screen_step_done')"
                />
                <item-detail-card
                    :key="make_state_component_key(['location_dest', state.data.move_line.location_dest.id])"
                    :record="state.data.move_line.location_dest"
                    :options="{title_action_field: {path: 'name', action_val_path: 'name'}}"
                    :card_color="utils.colors.color_for('screen_step_todo')"
                />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-back />
                        </v-col>
                    </v-row>
                </div>
            </template>
            <div v-if="state_in(['select_product', 'set_quantity'])" class="button-list button-vertical-list full">
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <cancel-button v-on:cancel="on_cancel"></cancel-button>
                    </v-col>
                </v-row>
            </div>
            <last-operation v-if="state_is('show_completion_info')" v-on:confirm="state.on_confirm"></last-operation>
        </Screen>
    `,
    methods: {
        screen_title: function () {
            if (_.isEmpty(this.current_doc()) || this.state_is("select_document")) {
                return this.menu_item().name;
            }
            const title = this.current_doc().record.name;
            return title;
        },
        current_doc: function () {
            const data = this.state_get_data("set_quantity");
            if (_.isEmpty(data)) {
                return null;
            }
            return {
                record: data.move_line.product,
                identifier: data.move_line.product.name,
            };
        },
        current_location: function () {
            const data = this.state_get_data("select_product");
            if (_.isEmpty(data) || _.isEmpty(data.location)) {
                return {};
            }
            return data.location;
        },
        current_location_msg: function () {
            if (this.current_location().id) {
                return {title: "Working from location " + this.current_location().name};
            }
            return {};
        },
        current_package: function () {
            const data = this.state_get_data("select_product");
            if (_.isEmpty(data) || _.isEmpty(data.package)) {
                return {};
            }
            return data.package;
        },
        current_package_msg: function () {
            if (this.current_package().id) {
                return {title: "Working on package " + this.current_package().name};
            }
            return {};
        },
        product_detail_options_for_set_quantity: function () {
            return {
                title_action_field: {action_val_path: "product.barcode"},
                key_title: "product.display_name",
                fields: [{path: "lot.name", label: "Lot", action_val_path: "lot.name"}],
            };
        },
        move_line_options_for_set_location: function () {
            return {
                key_title: "product.display_name",
                loud_labels: true,
                fields: [{path: "location_src.name", label: "Source Location"}],
            };
        },
        linear_progress_options_for_select_product: function () {
            return {
                done_label: "Ongoing",
                todo_label: "Available",
                color: "lime",
            };
        },
        get_select_product_scan_params: function (scanned) {
            const params = {
                barcode: scanned.text,
            };
            const state_location = _.result(this.state.data, "location", false);
            params.location_id = state_location.id;
            const state_package = _.result(this.state.data, "package", false);
            params.package_id = state_package.id;
            return params;
        },
        get_select_product_package_or_location_data: function () {
            if (this.state.data.package) {
                return this.state.data.package;
            }
            return this.state.data.location;
        },
        display_operations_progress: function () {
            const operation_progress = this._get_operation_progress_data();
            if (operation_progress) {
                return operation_progress.to_do > 0;
            }
        },
        _get_operation_progress_data: function () {
            return _.result(
                this.get_select_product_package_or_location_data(),
                "operation_progress",
                false
            );
        },
    },
    data: function () {
        return {
            usage: "single_product_transfer",
            initial_state_key: "select_location_or_package",
            states: {
                init: {
                    enter: () => {
                        this.wait_call(this.odoo.call("start"));
                    },
                },
                select_location_or_package: {
                    display_info: {
                        title: "Scan a location or a package",
                        scan_placeholder: "Scan location / package",
                    },
                    on_scan: (scanned) => {
                        this.wait_call(
                            this.odoo.call("scan_location_or_package", {
                                barcode: scanned.text,
                            })
                        );
                    },
                },
                select_product: {
                    display_info: {
                        title: "Select a product",
                        scan_placeholder: "Scan product / lot",
                    },
                    on_scan: (scanned) => {
                        const params = this.get_select_product_scan_params(scanned);
                        this.wait_call(this.odoo.call("scan_product", params));
                    },
                    on_cancel: () => {
                        this.wait_call(this.odoo.call("scan_product__action_cancel"));
                    },
                },
                set_quantity: {
                    display_info: {
                        title: "Set quantity",
                        scan_placeholder:
                            "Scan product / packaging / lot / location / package",
                    },
                    events: {
                        qty_edit: "on_qty_update",
                    },
                    on_qty_update: (qty) => {
                        this.state.data.quantity = qty;
                    },
                    on_scan: (scanned) => {
                        const confirmation = this.state.data.asking_confirmation
                            ? true
                            : false;
                        this.wait_call(
                            this.odoo.call("set_quantity", {
                                selected_line_id: this.state.data.move_line.id,
                                barcode: scanned.text,
                                quantity: this.state.data.quantity,
                                confirmation,
                            })
                        );
                    },
                    on_cancel: () => {
                        this.wait_call(
                            this.odoo.call("set_quantity__action_cancel", {
                                selected_line_id: this.state.data.move_line.id,
                            })
                        );
                    },
                },
                set_location: {
                    display_info: {
                        title: "Set location",
                        scan_placeholder: "Scan location",
                    },
                    on_scan: (scanned) => {
                        this.wait_call(
                            this.odoo.call("set_location", {
                                selected_line_id: this.state.data.move_line.id,
                                package_id: this.state.data.package.id,
                                barcode: scanned.text,
                            })
                        );
                    },
                    on_back: () => {
                        $instance.state_to("set_quantity");
                        $instance.reset_notification();
                    },
                },
                show_completion_info: {
                    on_confirm: () => {
                        this.state_to("select_location_or_package");
                    },
                },
            },
        };
    },
};

process_registry.add("single_product_transfer", SingleProductTransfer);

export default SingleProductTransfer;
