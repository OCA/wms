/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ScenarioBaseMixin} from "/shopfloor_mobile_base/static/wms/src/scenario/mixins.js";
import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

// TODO: consider replacing the dynamic "autofocus" in the searchbar by an event.
// At the moment, we need autofocus to be disabled if there's a user popup.
const LocationContentTransfer = {
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
                :autofocus="!screen_info.user_popup"
                />
            <template v-if="state_in(['scan_location']) && state.data.location">
                <item-detail-card
                    :key="make_state_component_key(['detail-move-line-location', state.data.location.id])"
                    :record="state.data.location"
                    :options="{main: true, key_title: 'name', title_action_field: {action_val_path: 'name'}}"
                    :card_color="utils.colors.color_for('screen_step_done')"
                />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <cancel-button v-on:cancel="on_cancel"/>
                        </v-col>
                    </v-row>
                </div>
            </template>

            <get-work
                v-if="state_is('get_work')"
                v-on:get_work="state.on_get_work"
                v-on:manual_selection="state.on_manual_selection"
            />

            <div v-if="state_in(['start_single', 'scan_destination', 'scan_destination_all']) && wrapped_context().has_records">

                <item-detail-card
                    v-if="wrapped_context().location_src"
                    :key="make_state_component_key(['detail-move-line-loc-src', wrapped_context().location_src.id])"
                    :record="wrapped_context().location_src"
                    :options="{main: true, key_title: 'name', title_action_field: {action_val_path: 'barcode'}}"
                    :card_color="utils.colors.color_for(state_in(['start_single', 'scan_destination', 'scan_destination_all']) ? 'screen_step_done': 'screen_step_todo')"
                    />

                <div v-for="rec in wrapped_context().records">

                    <!--batch-picking-line-detail
                        :line="rec"
                        :key="make_state_component_key(['detail-move-line', rec.id])"
                        :article-scanned="state_is('scan_destination')"
                        :show-qty-picker="state_is('scan_destination')"
                        :default-destination-key="'location_dest'"
                        /-->
                    <!--
                    TODO: "batch-picking-line-detail" has some limitations which would require more tweaking on options.
                    No time ATM to do that but the big TODO is: rename picking-line-detail to generic name and make it a bit more configurable
                    eg: display source location or destination location, control colors by step, etc.
                    Hence for now, we copy paste its code here and customize it for this case.
                    -->
                    <item-detail-card
                        :key="make_state_component_key(['detail-move-line-product', rec.id])"
                        :record="rec"
                        :options="utils.wms.move_line_product_detail_options(rec, {fields: [{path: 'picking.name', label: 'Picking'}]})"
                        :card_color="utils.colors.color_for(state_in(['scan_destination', 'scan_destination_all']) ? 'screen_step_done': 'screen_step_todo')"
                        />

                    <v-card v-if="wrapped_context()._type == 'move_line' && state_is('scan_destination')"
                            class="pa-2" :color="utils.colors.color_for('screen_step_todo')">
                        <packaging-qty-picker
                            :key="make_state_component_key(['packaging-qty-picker', rec.id])"
                            v-bind="utils.wms.move_line_qty_picker_props(rec)"
                            />
                    </v-card>

                    <line-actions-popup
                        v-if="!wrapped_context()._multi"
                        :line="rec"
                        :actions="line_actions()"
                        :key="make_state_component_key(['line-actions', rec.id])"
                        v-on:action="on_line_action"
                        />
                </div>

                <item-detail-card
                    v-if="wrapped_context().location_dest"
                    :key="make_state_component_key(['detail-move-line-loc-src', wrapped_context().location_dest.id])"
                    :record="wrapped_context().location_dest"
                    :options="{main: true, key_title: 'name', title_action_field: {action_val_path: 'barcode'}}"
                    :card_color="utils.colors.color_for('screen_step_todo')"
                    />

            </div>
            <line-stock-out
                v-if="state_is('stock_issue')"
                v-on:confirm_stock_issue="state.on_confirm_stock_issue"
                />
            <div class="button-list button-vertical-list full">
                <v-row align="center" v-if="state_is('scan_destination_all')">
                    <v-col class="text-center" cols="12">
                        <btn-action @click="state.on_split_by_line">Process by line</btn-action>
                    </v-col>
                </v-row>
            </div>
        </Screen>
        `,
    methods: {
        screen_title: function () {
            if (!this.has_picking()) return this.menu_item().name;
            return this.current_picking().name;
        },
        // TODO: if we have this working we can remove the picking detail?
        current_doc: function () {
            const picking = this.current_picking();
            return {
                record: picking,
                identifier: picking.name,
            };
        },
        // TODO: ask Joél if this is needed
        current_picking: function () {
            const data = this.state_get_data("start");
            if (_.isEmpty(data) || _.isEmpty(data.move_line.picking)) {
                return {};
            }
            return data.move_line.picking;
        },
        has_picking: function () {
            return !_.isEmpty(this.current_picking());
        },
        /**
         * As we can get `move_line` or `package_level` for single items
         * and `move_lines` or `package_levels` for multiple items,
         * this function tries to make such data homogenous.
         * We'll work alway with multiple records and loop on them.
         * TODO: this should be computed to be cached.
         */
        wrapped_context: function () {
            const data = this.state.data;
            const res = {
                has_records: true,
                records: [].concat(data.move_lines || [], data.package_levels || []),
                location_src: null,
                location_dest: null,
                _multi: true,
                _type: "mix",
            };
            if (_.isEmpty(res.records) && data.move_line) {
                res.records = [data.move_line];
                res._type = "move_line";
                res._multi = false;
            }
            if (_.isEmpty(res.records) && data.package_level) {
                res.records = [data.package_level];
                res._type = "pkg_level";
                res._multi = false;
            }
            res.has_records = res.records.length > 0;
            res.location_src = res.has_records ? res.records[0].location_src : null;
            res.location_dest = res.has_records ? res.records[0].location_dest : null;
            return res;
        },
        move_line_detail_list_options: function (move_line) {
            return this.utils.wms.move_line_product_detail_options(move_line, {
                loud_labels: true,
                fields_blacklist: ["product.qty_available"],
                fields: [{path: "location_src.name", label: "From"}],
            });
        },
        line_actions: function () {
            const actions = [
                {name: "Postpone line", event_name: "action_postpone"},
                {name: "Declare stock out", event_name: "action_stock_out"},
            ];
            if (this.state.data.package_level) {
                actions.push({name: "Open Package", event_name: "action_open_package"});
            }
            return actions;
        },
        // Common actions
        on_line_action: function (action) {
            this["on_" + action.event_name].call(this);
        },
        on_action_postpone: function () {
            let endpoint, endpoint_data;
            const data = this.state.data;
            if (data.package_level) {
                endpoint = "postpone_package";
                endpoint_data = {
                    package_level_id: data.package_level.id,
                    location_id: data.package_level.location_src.id,
                };
            } else {
                endpoint = "postpone_line";
                endpoint_data = {
                    move_line_id: data.move_line.id,
                    location_id: data.move_line.location_src.id,
                };
            }
            this.wait_call(this.odoo.call(endpoint, endpoint_data));
        },
        on_action_stock_out: function () {
            this.state_set_data(this.state.data, "stock_issue");
            this.state_to("stock_issue");
        },
        on_action_open_package: function () {
            const data = this.state.data;
            const endpoint_data = {
                location_id: data.package_level.location_src.id,
                package_level_id: data.package_level.id,
            };
            this.wait_call(this.odoo.call("dismiss_package_level", endpoint_data));
        },
    },
    data: function () {
        return {
            usage: "location_content_transfer",
            initial_state_key: "init",
            scan_destination_qty: 0,
            states: {
                init: {
                    enter: () => {
                        this.wait_call(this.odoo.call("start_or_recover"));
                    },
                },
                get_work: {
                    on_get_work: (evt) => {
                        this.wait_call(this.odoo.call("find_work"));
                    },
                    on_manual_selection: (evt) => {
                        this.state_to("scan_location");
                    },
                },
                scan_location: {
                    display_info: {
                        title: this.$t("location_content_transfer.scan_location.title"),
                        scan_placeholder: this.$t("scan_placeholder_translation"),
                    },
                    on_cancel: () => {
                        this.state_reset_data("scan_location");
                        this.wait_call(
                            this.odoo.call("cancel_work", {
                                location_id: this.state.data.location.id,
                            })
                        );
                    },
                    on_scan: (scanned) => {
                        this.wait_call(
                            this.odoo.call("scan_location", {barcode: scanned.text})
                        );
                    },
                },
                scan_destination_all: {
                    display_info: {
                        title: this.$t(
                            "location_content_transfer.scan_destination_all.title"
                        ),
                        scan_placeholder: this.$t("scan_placeholder_translation"),
                    },
                    on_scan: (scanned) => {
                        const data = this.state.data;
                        this.wait_call(
                            this.odoo.call("set_destination_all", {
                                location_id: data.location.id,
                                barcode: scanned.text,
                                confirmation: data.confirmation_required,
                            })
                        );
                    },
                    on_split_by_line: () => {
                        const location = this.state.data.location;
                        this.wait_call(
                            this.odoo.call("go_to_single", {location_id: location.id})
                        );
                    },
                },
                start_single: {
                    display_info: {
                        scan_placeholder: this.$t(
                            "location_content_transfer.start_single.scan_placeholder"
                        ),
                    },
                    on_scan: (scanned) => {
                        let endpoint, endpoint_data;
                        const data = this.state.data;
                        if (data.package_level) {
                            endpoint = "scan_package";
                            endpoint_data = {
                                package_level_id: data.package_level.id,
                                location_id: data.package_level.location_src.id,
                                barcode: scanned.text,
                            };
                        } else {
                            endpoint = "scan_line";
                            endpoint_data = {
                                move_line_id: data.move_line.id,
                                location_id: data.move_line.location_src.id,
                                barcode: scanned.text,
                            };
                        }
                        this.wait_call(this.odoo.call(endpoint, endpoint_data));
                    },
                },
                scan_destination: {
                    enter: () => {
                        this.reset_notification();
                    },
                    display_info: {
                        title: this.$t(
                            "location_content_transfer.scan_destination.title"
                        ),
                        scan_placeholder: this.$t("scan_placeholder_translation"),
                    },
                    events: {
                        qty_edit: "on_qty_update",
                    },
                    on_qty_update: (qty) => {
                        this.scan_destination_qty = parseInt(qty, 10);
                    },
                    on_scan: (scanned) => {
                        let endpoint, endpoint_data;
                        const data = this.state.data;
                        if (data.package_level) {
                            endpoint = "set_destination_package";
                            endpoint_data = {
                                package_level_id: data.package_level.id,
                                location_id: data.package_level.location_src.id,
                                barcode: scanned.text,
                                confirmation: data.confirmation_required,
                            };
                        } else {
                            endpoint = "set_destination_line";
                            endpoint_data = {
                                move_line_id: data.move_line.id,
                                location_id: data.move_line.location_src.id,
                                barcode: scanned.text,
                                confirmation: data.confirmation_required,
                                quantity: this.scan_destination_qty,
                            };
                        }
                        this.wait_call(this.odoo.call(endpoint, endpoint_data));
                    },
                    on_split_by_line: () => {
                        const location = this.state.data.move_lines[0].location_src;
                        this.wait_call(
                            this.odoo.call("go_to_single", {location_id: location.id})
                        );
                    },
                },
                stock_issue: {
                    enter: () => {
                        this.reset_notification();
                    },
                    on_confirm_stock_issue: () => {
                        let endpoint, endpoint_data;
                        const data = this.state.data;
                        if (data.package_level) {
                            endpoint = "stock_out_package";
                            endpoint_data = {
                                package_level_id: data.package_level.id,
                                location_id: data.package_level.location_src.id,
                            };
                        } else {
                            endpoint = "stock_out_line";
                            endpoint_data = {
                                move_line_id: data.move_line.id,
                                location_id: data.move_line.location_src.id,
                            };
                        }
                        this.wait_call(this.odoo.call(endpoint, endpoint_data));
                    },
                },
            },
        };
    },
};

process_registry.add("location_content_transfer", LocationContentTransfer);

export default LocationContentTransfer;
