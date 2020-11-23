/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ScenarioBaseMixin} from "/shopfloor_mobile_base/static/wms/src/scenario/mixins.js";
import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

const Reception = {
    mixins: [ScenarioBaseMixin],
    template: `
        <Screen :screen_info="screen_info">
            <choosing-reception-contact
                v-if="state_is('start')"
                @select-contact="state.onSelectContact"
                :partners="state.data.partners"
                :fields="state.fields"
                />
            <choosing-reception-picking
                v-if="state_is('manual_selection')"
                @select-picking="state.onSelectPicking"
                :stateData="state"
                />
            <reception-scanning-product
                v-if="state_is('scan_products')"
                :stateData="state"
                @found="state.onScanProduct"
                />
            <div
                v-if="state_is('scan_products')"
                style="position: fixed; bottom: 0; right: 12px;width: 100%"
            >
                <v-row>
                    <v-col
                        class="d-flex justify-end"
                        >
                        <v-btn
                            x-large
                            class="justify-end"
                            @click="state.onFinish"
                            :disabled="state.data.move_lines_picking.length !== 0"
                            :color="utils.colors.color_for('accent')">
                            Finish reception
                        </v-btn>
                    </v-col>
                </v-row>
            </div>
        </Screen>
    `,
    mounted() {},
    computed: {
        partnerId: function() {
            return this.state.data.id;
        },
    },
    data: function() {
        return {
            usage: "reception",
            initial_state_key: "start",
            scan_destination_qty: 0,
            errorNotFound: undefined,
            states: {
                start: {
                    onSelectContact: partner_id => {
                        this.wait_call(this.odoo.call("list_move_lines", {partner_id}));
                    },
                    fields: [
                        {
                            label: "Total receipt",
                            path: "picking_count",
                        },
                    ],
                    enter: () => {
                        if (!this.state_get_data("start").partners) {
                            this.wait_call(this.odoo.call("list_vendor_with_pickings"));
                        }
                    },
                },
                scan_products: {
                    scanned: [],
                    productQtyFields: [
                        {
                            label: "Qty",
                            path: "qty",
                        },
                    ],
                    pickingFields: [
                        {
                            label: "Qty",
                            path: "qtyDone",
                        },
                    ],
                    pickedFields: [
                        {
                            label: "Qty",
                            path: "qtyDone",
                        },
                        {
                            label: "Product is in",
                            path: "dest",
                        },
                    ],
                    receptionFields: [
                        {
                            label: "Partner",
                            path: "partner.name",
                        },
                    ],
                    display_info: {
                        scan_placeholder: () => {
                            if (this.state.data.move_lines_picking.length === 0) {
                                return "Scan a product";
                            }
                            if (this.state.data.move_lines_picking.length > 0) {
                                return `Scan a product ${this.state.data.move_lines_picking[0].product.name}, a quantity or a destination`;
                            }
                        },
                    },
                    onFinish: () => {
                        this.wait_call(
                            this.odoo.call("finish_receipt", {
                                partner_id: this.partnerId,
                                move_lines_picked: this.state.data.move_lines_picked.map(
                                    line => line.id
                                ),
                            })
                        );
                    },
                    onScanProduct: ({text: barcode}) => {
                        const intInText =
                            "" + barcode == parseInt(barcode, 10) &&
                            parseInt(barcode, 10);
                        const {move_lines_picking} = this.state.data;

                        if (move_lines_picking.length > 0) {
                            if (!isNaN(intInText) && intInText === 0) {
                                this.wait_call(
                                    this.odoo.call("reset_product", {
                                        partner_id: this.partnerId,
                                        barcode,
                                        move_lines_picking: move_lines_picking.map(
                                            line => line.id
                                        ),
                                    })
                                );
                            } else if (
                                !isNaN(intInText) &&
                                intInText > 0 &&
                                intInText < 10000
                            ) {
                                this.wait_call(
                                    this.odoo.call("set_quantity", {
                                        partner_id: this.partnerId,
                                        move_lines_picking: move_lines_picking.map(
                                            line => line.id
                                        ),
                                        qty: intInText,
                                    })
                                );
                            } else if (
                                barcode === move_lines_picking[0].product.barcode ||
                                (move_lines_picking[0].product.barcodes &&
                                    move_lines_picking[0].product.barcodes.findIndex(
                                        b => b.name === barcode
                                    ) !== -1)
                            ) {
                                this.wait_call(
                                    this.odoo.call("scan_product", {
                                        partner_id: this.partnerId,
                                        barcode,
                                    })
                                );
                            } else {
                                this.wait_call(
                                    this.odoo.call("set_destination", {
                                        partner_id: this.partnerId,
                                        barcode,
                                        move_lines_picking: move_lines_picking.map(
                                            line => line.id
                                        ),
                                        location_dest: barcode,
                                    })
                                );
                            }
                        } else {
                            this.wait_call(
                                this.odoo.call("scan_product", {
                                    partner_id: this.partnerId,
                                    barcode,
                                })
                            );
                        }
                    },
                },
            },
        };
    },
};

process_registry.add("reception", Reception);

export default Reception;
