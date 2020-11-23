/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ScenarioBaseMixin} from "/shopfloor_mobile_base/static/wms/src/scenario/mixins.js";
import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

const CheckoutScanAndPack = {
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
                :fields="state.fields"
                :refocusInput="true"
                />
            <div v-if="state_is('start') && state.data.pickings && state.data.pickings.length === 0">There is nothing to pack</div>
            <detail-simple-picking
                @click="state.on_scan({text: picking.name})"
                v-if="state_is('start')"
                v-for="picking in state.data.pickings"
                :key="picking.id"
                :record="picking"
                :options="state.options"
                />
            <scan-products
                v-if="state_is('scan_products')"
                :products="state.data.picking.move_lines"
                :fields="state.fields"
                :lastScanned="lastScanned"
                :packing="state.data.picking"
                v-on:shippedFinished="state.shipFinished"
                v-on:shippedUnfinished="state.shipUnfinished"
                v-on:skipPack="state.skipPack"
                />
            <v-dialog
                v-model="is_confirming()"
                max-width="380"
            >
                <user-confirmation
                    title="Confirm unfinished shipping"
                    question="Are you sure you want to ship that package unfinished ?"
                    @user-confirmation="state.on_confirm"
                />
            </v-dialog>
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
    methods: {
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
        is_confirming: function() {
            return this.state_is("scan_products") && this.confirming;
        },
    },
    data: function() {
        return {
            usage: "checkout_scan_and_pack",
            initial_state_key: "start",
            lastScanned: null,
            confirming: false,
            states: {
                scan_products: {
                    on_scan: scanned => {
                        const intInText = parseInt(scanned.text);
                        if (
                            !isNaN(intInText) &&
                            intInText < 10000 &&
                            this.lastScanned
                        ) {
                            const moveLinesSelected = this.state.data.picking.move_lines.filter(
                                line =>
                                    line.product.barcode === this.lastScanned &&
                                    !line.done
                            );

                            if (moveLinesSelected.length > 0) {
                                this.wait_call(
                                    this.odoo.call("set_quantity", {
                                        barcode: this.lastScanned,
                                        picking_id: this.state.data.picking.id,
                                        move_line_id: moveLinesSelected[0].id,
                                        qty: intInText,
                                    })
                                );

                                if (intInText === 0) {
                                    this.lastScanned = null;
                                }
                            } else {
                                this.set_message({
                                    message_type: "error",
                                    body: "An error as occured please scan a product",
                                });
                                this.lastScanned = null;
                            }
                        } else {
                            this.wait_call(
                                this.odoo.call("scan_product", {
                                    barcode: scanned.text,
                                    picking_id: this.state.data.picking.id,
                                }),
                                {
                                    callback: ({message}) => {
                                        if (
                                            !message ||
                                            message.message_type !== "error"
                                        ) {
                                            this.lastScanned = scanned.text;
                                        }
                                    },
                                }
                            );
                        }
                    },
                    shipFinished: () => {
                        this.wait_call(
                            this.odoo.call("done", {
                                picking_id: this.state.data.picking.id,
                            })
                        );
                        this.lastScanned = null;
                    },
                    shipUnfinished: () => {
                        this.wait_call(
                            this.odoo.call("done", {
                                picking_id: this.state.data.picking.id,
                            }),
                            {
                                callback: ({data}) => {
                                    this.confirming = true;
                                },
                            }
                        );
                        this.lastScanned = null;
                    },
                    skipPack: () => {
                        this.wait_call(
                            this.odoo.call("scan_document", {
                                barcode: this.state.data.picking.move_lines[0]
                                    .location_src.barcode,
                                skip: parseInt(this.state.data.skip || 0) + 1,
                            })
                        );
                        this.lastScanned = null;
                    },
                    display_info: {
                        scan_placeholder: "Barcode or quantity",
                    },
                    fields: [
                        {path: "supplierCode", label: "Vendor code", klass: "loud"},
                        {path: "qty", label: "Quantity"},
                        {path: "qtyDone", label: "Done"},
                    ],
                    on_confirm: confirm => {
                        if (confirm === "yes") {
                            this.wait_call(
                                this.odoo.call("done", {
                                    picking_id: this.state.data.picking.id,
                                    confirmation: true,
                                })
                            );
                            this.confirming = false;
                        } else {
                            this.confirming = false;
                        }
                    },
                    enter: () => {
                        this.confirming = this.state.data.confirm;
                    },
                },
                start: {
                    options: {
                        loud_title: true,
                        fields: [
                            {path: "partner.name"},
                            {path: "origin"},
                            {path: "carrier.name", label: "Carrier"},
                            {path: "move_line_count", label: "Lines"},
                        ],
                    },
                    display_info: {
                        title: "Choose an order to pack",
                        scan_placeholder: "Scan pack / picking / location",
                    },
                    on_scan: ({text}) => {
                        this.wait_call(
                            this.odoo.call("scan_document", {
                                barcode: text,
                                skip: this.$route.query.skip,
                            })
                        );
                    },
                    enter: () => {
                        this.wait_call(this.odoo.call("list_stock_picking"), {
                            keepMessage: true,
                        });
                    },
                },
            },
        };
    },
};

process_registry.add("checkout_scan_and_pack", CheckoutScanAndPack);

export default CheckoutScanAndPack;
