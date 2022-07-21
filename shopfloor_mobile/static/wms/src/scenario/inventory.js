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
                        :options="{main: true, key_title: 'location_id.name'}"
                        />
                </div>
            </div>
            <div v-for="line in state.data.lines">
                <inventory-location-detail
                    v-if="state_is('scan_product')"
                    :line="state.data"
                    :article-scanned="state_is('scan_product')"
                    :show-qty-picker="state_is('scan_product')"
                    />
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
                            <v-btn color="default" @click="state.on_back">Back</v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>

            <div class="button-list button-vertical-list full">
                <v-row align="center" v-if="state_is('scan_product')">
                    <v-col class="text-center" cols="12">
                        <btn-back />
                    </v-col>
                </v-row>
            </div>

        </Screen>
    `,
    computed: {
        manual_select_inventory_fields: function () {
            return [{path: "id", label: "Id"}];
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
            if (data === "done") {
                color = "success";
            }
            console.log("color");
            console.log(color);
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
                        this.scan_product_qty = this.state_get_data(
                            "start_location"
                        ).quantity;
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
                                quantity: this.scan_product_qty,
                            })
                        );
                    },
                },
            },
        };
    },
};

process_registry.add("inventory", Inventory);

export default Inventory;
