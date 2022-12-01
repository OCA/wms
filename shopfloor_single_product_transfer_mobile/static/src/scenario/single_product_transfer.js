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
                v-if="state_in(['select_location', 'select_product', 'set_quantity'])"
                v-on:found="on_scan"
                :input_placeholder="search_input_placeholder"
            />
            <template v-if="state_is('select_product')">
                <item-detail-card
                    :key="make_state_component_key(['location_src', state.data.location.id])"
                    :record="state.data.location"
                    :card_color="utils.colors.color_for('screen_step_done')"
                />
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
        product_detail_options_for_set_quantity: function () {
            return {
                title_action_field: {action_val_path: "product.barcode"},
                key_title: "product.display_name",
                fields: [{path: "lot.name", label: "Lot", action_val_path: "lot.name"}],
            };
        },
    },
    data: function () {
        return {
            usage: "single_product_transfer",
            initial_state_key: "select_location",
            states: {
                init: {
                    enter: () => {
                        this.wait_call(this.odoo.call("start"));
                    },
                },
                select_location: {
                    display_info: {
                        title: "Scan a location",
                        scan_placeholder: "Scan location",
                    },
                    on_scan: (scanned) => {
                        this.wait_call(
                            this.odoo.call("scan_location", {
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
                        this.wait_call(
                            this.odoo.call("scan_product", {
                                location_id: this.state.data.location.id,
                                barcode: scanned.text,
                            })
                        );
                    },
                    on_cancel: () => {
                        this.wait_call(this.odoo.call("scan_product__action_cancel"));
                    },
                },
                set_quantity: {
                    display_info: {
                        title: "Set quantity",
                        scan_placeholder: "Scan product / package / lot / location",
                    },
                    on_scan: (scanned) => {
                        this.wait_call(
                            this.odoo.call("set_quantity", {
                                selected_line_id: this.state.data.move_line.id,
                                barcode: scanned.text,
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
                show_completion_info: {
                    on_confirm: () => {
                        this.state_to("select_location");
                    },
                },
            },
        };
    },
};

process_registry.add("single_product_transfer", SingleProductTransfer);

export default SingleProductTransfer;
