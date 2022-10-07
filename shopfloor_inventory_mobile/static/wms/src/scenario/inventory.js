/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Benoît Guillot <benoit.guillot@akretion.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ScenarioBaseMixin} from "/shopfloor_mobile_base/static/wms/src/scenario/mixins.js";
import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

const Inventory = {
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
            <get-work
                v-if="state_is('start')"
                v-on:get_work="state.on_get_work"
                v-on:manual_selection="state.on_manual_selection"
                />
            <inventory-detail
                v-if="state_is('confirm_start')"
                :record="state.data"
                v-on:confirm="state.on_confirm"
                v-on:cancel="state.on_cancel"
                />
            <div v-if="state_is('start_location')">
                <div v-for="loc in state.data.locations">
                    <item-detail-card
                        :key="make_state_component_key(['location-state', loc.location.id])"
                        :card_color="utils.colors.color_for(location_state_color(loc.state))"
                        :record="loc"
                        :options="{main: true, key_title: 'location.name'}"
                        />
                </div>
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn color="accent" @click="state.on_done">{{ $t('inventory.button.done') }}</v-btn>
                        </v-col>
                    </v-row>
                </div>
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn color="default" @click="state.on_back">{{ $t('inventory.button.back') }}</v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>

            <div v-if="state_is('scan_product')" >
                <div v-if="_.result(state, 'data.current_line')" >
                    <inventory-line-detail
                        v-if="state_is('scan_product')"
                        :line="state.data.current_line"
                        :article-scanned="state_is('scan_product')"
                        :show-qty-picker="state_is('scan_product')"
                        v-on:confirm="state.on_confirm_qty"
                        />
                </div>
                <div v-for="line in state.data.lines">
                    <item-detail-card
                        :key="make_state_component_key(['inventory-line-state', line.product.id])"
                        :card_color="utils.colors.color_for(line_state_color(line))"
                        :record="line"
                        :options="{main: true, key_title: 'product.name'}"
                        />
                </div>
                <div v-if="_.isEmpty(_.result(state, 'data.lines')) && _.isEmpty(_.result(state, 'data.current_line')) && _.result(state, 'data.display_location_content')" >
                    <v-card :color="utils.colors.color_for('screen_step_todo')">
                        <v-card-title>
                            <p> {{ $t('inventory.message.location_empty') }} </p>
                        </v-card-title>
                    </v-card>
                    <div class="button-list button-vertical-list full">
                        <v-row align="center">
                            <v-col class="text-center" cols="12">
                                <btn-action action="todo" @click="state.on_confirm_empty">{{ $t('inventory.button.confirm') }}</btn-action>
                            </v-col>
                        </v-row>
                    </div>
                </div>
                <div v-if="_.result(state, 'data.current_line')" >
                    <div class="button-list button-vertical-list full">
                        <v-row align="center">
                            <v-col class="text-center" cols="12">
                                <btn-action action="todo" @click="state.on_confirm_qty">{{ $t('inventory.button.confirm_qty') }}</btn-action>
                            </v-col>
                        </v-row>
                    </div>
                </div>
                <div v-if="(!_.isEmpty(_.result(state, 'data.lines')) && _.isEmpty(_.result(state, 'data.current_line'))) || !_.result(state, 'data.display_location_content')" >
                    <div class="button-list button-vertical-list full">
                        <v-row align="center">
                            <v-col class="text-center" cols="12">
                                <btn-action action="todo" @click="state.on_confirm">{{ $t('inventory.button.confirm') }}</btn-action>
                            </v-col>
                        </v-row>
                    </div>
                </div>
            </div>

            <div v-if="state_is('manual_selection')">
                <manual-select
                    v-on:select="state.on_select"
                    v-on:back="state.on_back"
                    :records="state.data.records"
                    :list_item_fields="manual_select_inventory_fields"
                    />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn color="default" @click="state.on_back">{{ $t('inventory.button.back') }}</v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>

           <div v-if="state_is('confirm_done')" >
               <div class="button-list button-vertical-list full">
                   <v-row align="center">
                       <v-col class="text-center" cols="12">
                           <btn-action action="todo" @click="state.on_confirm">{{ $t('inventory.button.confirm') }}</btn-action>
                       </v-col>
                   </v-row>
               </div>
            </div>

            <div class="button-list button-vertical-list full">
                <v-row align="center" v-if="state_is('confirm_done')">
                    <v-col class="text-center" cols="12">
                        <btn-back />
                    </v-col>
                </v-row>
            </div>

        </Screen>
    `,
    computed: {
        manual_select_inventory_fields: function () {
            return [
                {
                    path: "location_count",
                    label: this.$t("inventory.field.total_locations"),
                },
                {
                    path: "remaining_location_count",
                    label: this.$t("inventory.field.remaining_locations"),
                },
                {
                    path: "inventory_line_count",
                    label: this.$t("inventory.field.total_lines"),
                },
            ];
        },
    },
    methods: {
        screen_title: function () {
            if (_.isEmpty(this.current_inventory()) || this.state_is("confirm_start"))
                return this.menu_item().name;
            let title = this.current_inventory().name;
            const location = this.current_location();
            if (location) {
                title += " > " + location.name;
            }
            return title;
        },
        current_inventory: function () {
            return this.state_get_data("confirm_start");
        },
        current_location: function () {
            const data = this.state_get_data("scan_product") || {};
            if (!data.location) {
                return null;
            }
            return data.location;
        },
        current_line: function () {
            const data = this.state_get_data("scan_product") || {};
            if (!data.current_line) {
                return null;
            }
            return data.current_line;
        },
        current_doc: function () {
            const location = this.current_location();
            if (!location) {
                return {};
            }
            return {
                record: location,
                identifier: location.name,
            };
        },
        location_state_color: function (data) {
            var color = "";
            if (data === "pending") {
                color = "warning";
            }
            if (data === "started") {
                color = "accent";
            }
            if (data === "done") {
                color = "success";
            }
            return color;
        },
        line_state_color: function (data) {
            var color = "";
            if (data.product_qty === 0) {
                color = "warning";
            } else {
                if (data.theoretical_qty === data.product_qty) {
                    color = "success";
                } else {
                    color = "error";
                }
            }
            return color;
        },
    },
    data: function () {
        // TODO: add a title to each screen
        return {
            usage: "inventory",
            initial_state_key: "start",
            scan_product_qty: 0,
            states: {
                start: {
                    on_get_work: (evt) => {
                        this.wait_call(this.odoo.call("find_inventory"));
                    },
                    on_manual_selection: (evt) => {
                        this.wait_call(this.odoo.call("list_inventory"));
                    },
                },
                manual_selection: {
                    on_back: () => {
                        this.state_to("start");
                        this.reset_notification();
                    },
                    on_select: (selected) => {
                        this.wait_call(
                            this.odoo.call("select_inventory", {
                                inventory_id: selected.id,
                            })
                        );
                    },
                    display_info: {
                        title: this.$t("inventory.manual_selection.title"),
                    },
                },
                confirm_start: {
                    on_cancel: () => {
                        this.state_to("start");
                        this.reset_notification();
                    },
                    on_confirm: () => {
                        console.log(this.current_inventory().id);
                        this.wait_call(
                            this.odoo.call("confirm_start", {
                                inventory_id: this.current_inventory().id,
                            })
                        );
                    },
                },
                start_location: {
                    display_info: {
                        title: this.$t("inventory.start_location.title"),
                        scan_placeholder: this.$t(
                            "inventory.start_location.scan_placeholder"
                        ),
                    },
                    on_scan: (scanned) => {
                        this.wait_call(
                            this.odoo.call("start_location", {
                                inventory_id: this.current_inventory().id,
                                barcode: scanned.text,
                            })
                        );
                    },
                    on_done: () => {
                        this.wait_call(
                            this.odoo.call("done_inventory", {
                                inventory_id: this.current_inventory().id,
                            })
                        );
                    },
                    on_back: () => {
                        this.state_to("start");
                        this.reset_notification();
                    },
                    // Additional actions
                    on_action: (action) => {
                        this.state["on_" + action].call(this);
                    },
                },
                scan_product: {
                    display_info: {
                        title: this.$t("inventory.scan_product.title"),
                        scan_placeholder: this.$t(
                            "inventory.scan_product.scan_placeholder"
                        ),
                    },
                    events: {
                        qty_edit: "on_qty_edit",
                    },
                    enter: () => {
                        // TODO: shalle we hook v-model for qty input straight to the state data?
                        this.scan_product_qty = this.current_line()
                            ? this.current_line().product_qty
                            : 0;
                    },
                    on_qty_edit: (qty) => {
                        this.scan_product_qty = parseInt(qty, 10);
                    },
                    on_scan: (scanned) => {
                        this.wait_call(
                            this.odoo.call("scan_product", {
                                inventory_id: this.current_inventory().id,
                                location_id: this.current_location().id,
                                barcode: scanned.text,
                                line_id: this.current_line()
                                    ? this.current_line().id
                                    : null,
                                quantity: this.scan_product_qty,
                            })
                        );
                        this.scan_product_qty = 0;
                    },
                    on_confirm_qty: () => {
                        this.wait_call(
                            this.odoo.call("confirm_line_qty", {
                                inventory_id: this.current_inventory().id,
                                location_id: this.current_location().id,
                                line_id: this.current_line().id,
                                quantity: this.scan_product_qty,
                            })
                        );
                        this.scan_product_qty = 0;
                    },
                    on_confirm_empty: () => {
                        this.wait_call(
                            this.odoo.call("location_inventoried", {
                                inventory_id: this.current_inventory().id,
                                location_id: this.current_location().id,
                                confirmation: true,
                            })
                        );
                    },
                    on_confirm: () => {
                        this.wait_call(
                            this.odoo.call("location_inventoried", {
                                inventory_id: this.current_inventory().id,
                                location_id: this.current_location().id,
                                confirmation: false,
                            })
                        );
                    },
                },
                confirm_done: {
                    display_info: {
                        title: this.$t("inventory.confirm_done.title"),
                    },
                    events: {
                        go_back: "on_back",
                    },
                    on_confirm: () => {
                        this.wait_call(
                            this.odoo.call("location_inventoried", {
                                inventory_id: this.current_inventory().id,
                                location_id: this.current_location().id,
                                confirmation: true,
                            })
                        );
                    },
                    on_back: () => {
                        this.state_to("scan_product");
                        this.reset_notification();
                    },
                },
            },
        };
    },
};

process_registry.add("inventory", Inventory);

export default Inventory;
