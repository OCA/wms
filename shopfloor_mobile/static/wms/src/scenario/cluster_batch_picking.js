import {ScenarioBaseMixin} from "/shopfloor_mobile_base/static/wms/src/scenario/mixins.js";
import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

const ClusterBatchPicking = {
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
                :refocusInput="true"
                />
            <get-work
                v-if="state_is('start')"
                v-on:get_work="state.on_get_work"
                v-on:manual_selection="state.on_manual_selection"
                />
            <batch-picking-detail
                v-if="state_is('confirm_start')"
                :record="state.data"
                v-on:confirm="state.on_confirm"
                v-on:cancel="state.on_cancel"
                />
            <batch-picking-line-detail
                v-if="state_in(['start_line', 'scan_destination', 'change_pack_lot', 'stock_issue'])"
                :line="state.data"
                :article-scanned="state_is('scan_destination')"
                :show-qty-picker="state_is('scan_destination')"
                />
            <batch-move-line
                v-if="state_is('scan_products')"
                :moveLines="state.data.move_lines"
                :fields="state.fields"
                :lastScanned="lastScanned"
                :selectedLocation="selectedLocation"
                :currentLocation="currentLocation"
                :lastPickedLine="lastPickedLine"
                @action="state.actionStockOut"
                />
            <batch-picking-line-actions
                v-if="state_is('start_line')"
                v-on:action="state.on_action"
                :line="state_get_data('start_line')"
                />
            <div v-if="state_is('scan_destination')">
                <div class="button-list button-vertical-list full mt-10">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn @click="state.on_action_full_bin">
                                Full bin
                            </v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>
            <stock-zero-check
                v-if="state_is('zero_check')"
                v-on:action="state.on_action"
                />

            <line-stock-out
                v-if="state_is('stock_issue')"
                v-on:confirm_stock_issue="state.on_confirm_stock_issue"
                />

            <div v-if="state_is('manual_selection')">
                <manual-select
                    v-on:select="state.on_select"
                    v-on:back="state.on_back"
                    :records="state.data.records"
                    :list_item_fields="manual_select_picking_fields"
                    />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn color="default" @click="state.on_back">Back</v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>

            <div class="unload-all" v-if="state_is('unload_all')">
                <v-card class="main">
                    <v-card-title>
                        <div class="main-info">
                            <div class="destination">
                                <span class="label">Destination:</span>
                                {{ state.data.location_dest.name }}
                            </div>
                        </div>
                    </v-card-title>
                </v-card>
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn color="primary" @click="$emit('action', 'action_split')">Split [TODO]</v-btn>
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
        manual_select_picking_fields: function() {
            return [
                {path: "picking_count", label: "Operations"},
                {path: "move_line_count", label: "Lines"},
            ];
        },
    },
    methods: {
        screen_title: function() {
            if (_.isEmpty(this.current_batch()) || this.state_is("confirm_start"))
                return this.menu_item().name;
            let title = this.current_batch().name;
            const picking = this.current_picking();
            if (picking) {
                title += " > " + picking.name;
            }
            return title;
        },
        current_batch: function() {
            return this.state_get_data("confirm_start");
        },
        current_picking: function() {
            const data = this.state_get_data("start_line") || {};
            if (!data.picking) {
                return null;
            }
            return data.picking;
        },
        action_full_bin: function() {
            this.wait_call(
                this.odoo.call("prepare_unload", {
                    picking_batch_id: this.current_batch().id,
                })
            );
        },
        find_move_line: function(move_lines, barcode, filter = () => true) {
            let move_line;

            move_lines.filter(filter).forEach(line => {
                if (line.product.barcode === barcode) {
                    move_line = move_line !== undefined ? move_line : line;
                }
            });

            return move_line || {};
        },
        find_src_location: function(move_lines, barcode, filter = () => true) {
            let location_src = "";

            move_lines.filter(filter).forEach(line => {
                if (line.location_src.barcode === barcode) {
                    location_src = line.location_src.id;
                }
            });

            return location_src;
        },
        handle_product_move_line: function({
            scanned,
            move_line,
            last_move_line,
        }) {
            if (last_move_line.id === move_line.id) {
                this.wait_call(
                    this.odoo.call("scan_product", {
                        barcode: scanned.text,
                        move_line_id: move_line.id,
                        picking_batch_id: this.state.data.id,
                        location_id: this.selectedLocation,
                        qty: 1,
                    }),
                    result => {
                        if (
                            !result.message ||
                            result.message.message_type !== "error"
                        ) {
                            this.lastScanned = scanned.text;
                        }
                    }
                );
            } else if (!last_move_line.id) {
                this.wait_call(
                    this.odoo.call("set_quantity", {
                        barcode: scanned.text,
                        move_line_id: move_line.id,
                        picking_batch_id: this.state.data.id,
                        location_id: this.selectedLocation,
                        qty: 1,
                    }),
                    result => {
                        if (
                            !result.message ||
                            result.message.message_type !== "error"
                        ) {
                            this.lastScanned = scanned.text;
                        }
                    }
                );
            }
            else {
                this.set_message({
                    message_type: "error",
                    body: `You can't scan another product before scanning a package or destination location`,
                });
            }
        },
        on_scan_with_selected_location: function ({
            scanned,
            move_line,
            last_move_line,
            intInText,
        }) {
            if (move_line.id) {
                this.handle_product_move_line({
                    scanned,
                    move_line,
                    last_move_line,
                });
            } else {
                if (!isNaN(intInText) && intInText === 0) {
                    this.wait_call(
                        this.odoo.call("set_quantity", {
                            barcode: this.lastScanned,
                            picking_batch_id: this.state.data.id,
                            move_line_id: last_move_line.id,
                            location_id: this.selectedLocation,
                            qty: intInText,
                        })
                    );

                    this.lastScanned = null;
                    this.selectedLocation = null;
                } else if (
                    !isNaN(intInText) &&
                    intInText > 0 &&
                    intInText < 10000 &&
                    this.lastScanned
                ) {
                    this.wait_call(
                        this.odoo.call("set_quantity", {
                            barcode: this.lastScanned,
                            picking_batch_id: this.state.data.id,
                            move_line_id: last_move_line.id,
                            location_id: this.selectedLocation,
                            qty: intInText,
                        })
                    );
                } else if (last_move_line.id) {
                    this.wait_call(
                        this.odoo.call("set_destination", {
                            barcode: scanned.text,
                            move_line_id: last_move_line.id,
                            picking_batch_id: this.state.data.id,
                            qty: last_move_line.qty_done,
                        }),
                        result => {
                            if (
                                result.message &&
                                result.message.message_type ===
                                    "success"
                            ) {
                                this.lastScanned = null;
                                this.selectedLocation = null;
                                this.lastPickedLine = last_move_line.id;
                            }
                        }
                    );
                }
            }
        },
    },
    data: function() {
        // TODO: add a title to each screen
        return {
            usage: "cluster_batch_picking",
            initial_state_key: "start",
            scan_destination_qty: 0,
            currentLocation: null,
            lastPickedLine: null,
            states: {
                start: {
                    on_get_work: evt => {
                        this.wait_call(this.odoo.call("find_batch"));
                    },
                    on_manual_selection: evt => {
                        this.wait_call(this.odoo.call("list_batch"));
                    },
                },
                manual_selection: {
                    on_back: () => {
                        this.state_to("start");
                        this.reset_notification();
                    },
                    on_select: selected => {
                        this.wait_call(
                            this.odoo.call("select", {
                                picking_batch_id: selected.id,
                            })
                        );
                    },
                    display_info: {
                        title: "Select a batch and start",
                    },
                },
                confirm_start: {
                    on_confirm: () => {
                        this.wait_call(
                            this.odoo.call("confirm_start", {
                                picking_batch_id: this.current_batch().id,
                            })
                        );
                    },
                    on_cancel: () => {
                        const self = this;
                        this.wait_call(
                            this.odoo.call("unassign", {
                                picking_batch_id: this.current_batch().id,
                            })
                        ).then(function() {
                            self.state_reset_data_all();
                        });
                    },
                },
                scan_products: {
                    actionStockOut: ({move_line_id, event_name}) => {
                        if (event_name === "actionStockOut") {
                            this.wait_call(
                                this.odoo.call("stock_issue", {
                                    move_line_id,
                                    picking_batch_id: this.state.data.id,
                                })
                            );
                        } else if (event_name === "cancelLine") {
                            this.wait_call(
                                this.odoo.call("cancel_line", {
                                    move_line_id,
                                    picking_batch_id: this.state.data.id,
                                })
                            );
                        }
                    },
                    on_scan: scanned => {
                        const intInText =
                            "" + scanned.text == parseInt(scanned.text, 10) &&
                            parseInt(scanned.text, 10);
                        let move_line = this.find_move_line(
                            this.state.data.move_lines,
                            scanned.text,
                            line => !line.done
                        );
                        let last_move_line = this.find_move_line(
                            this.state.data.move_lines,
                            this.lastScanned,
                            line => !line.done
                        );

                        //0) Nothing selected:
                        //  * Scan a source location -> A
                        //A) Source Location selected:
                        //  * Scan a product -> B
                        //  * Scan another source location -> A
                        //B) Source location selected and product scanned:
                        //  * Scan destination -> split line if quantity isn't enough -> 0

                        const selectedLocation = this.find_src_location(
                            this.state.data.move_lines,
                            scanned.text,
                            line => !line.done
                        );

                        if (selectedLocation && !last_move_line.id) {
                            this.selectedLocation = selectedLocation;
                            this.currentLocation = selectedLocation;
                            this.reset_notification();
                        } else if (this.selectedLocation) {
                            this.on_scan_with_selected_location({
                                scanned,
                                move_line,
                                last_move_line,
                                intInText,
                            });
                        } else {
                            //If there is no selected location, select a location
                            const selectedFromAllLocation = this.find_src_location(
                                this.state.data.move_lines,
                                scanned.text
                            );

                            //If we do not find a location or it is not a valid location
                            //display the proper error
                            if (selectedFromAllLocation === "") {
                                this.set_message({
                                    message_type: "error",
                                    body: "You need to scan a source location",
                                });
                            } else {
                                this.set_message({
                                    message_type: "error",
                                    body: `You can't select this location`,
                                });
                            }
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
                            })
                        );
                        this.lastScanned = null;
                    },
                    skipPack: () => {
                        this.lastScanned = null;
                        this.state_to("select_document", {
                            skip: parseInt(this.$route.query.skip || 0) + 1,
                        });
                    },
                    display_info: {
                        scan_placeholder: () =>
                            `Scan a ${!this.selectedLocation ? "source location" : ""}${
                                this.selectedLocation && !this.lastScanned
                                    ? "Product"
                                    : ""
                            }${
                                this.selectedLocation && this.lastScanned
                                    ? "Quantity, package or destination location"
                                    : ""
                            }`,
                    },
                    fields: [
                        {path: "supplierCode", label: "Vendor code", klass: "loud"},
                        {path: "qty", label: "Quantity"},
                        {path: "qtyDone", label: "Done"},
                        {path: "picking_dest.name", label: "Picking destination"},
                        {path: "dest.name", label: "Should be put in"},
                    ],
                    exit: () => {
                        this.lastScanned = null;
                        this.lastPickedLine = null;
                        this.currentLocation = null;
                        this.selectedLocation = null;
                    }
                },
                unload_all: {
                    display_info: {
                        title: "Unload all bins",
                        scan_placeholder: "Scan location",
                    },
                    on_scan: (scanned, confirmation = false) => {
                        this.state_set_data({location_barcode: scanned.text});
                        this.wait_call(
                            this.odoo.call("set_destination_all", {
                                picking_batch_id: this.current_batch().id,
                                barcode: scanned.text,
                                confirmation: confirmation,
                            })
                        );
                    },
                    on_action_split: () => {
                        this.wait_call(
                            this.odoo.call("unload_split", {
                                picking_batch_id: this.current_batch().id,
                                barcode: scanned.text, // TODO: should get barcode -> which one? See py specs
                            })
                        );
                    },
                },
                confirm_unload_all: {
                    display_info: {
                        title: "Unload all bins confirm",
                        scan_placeholder: "Scan location",
                    },
                    on_user_confirm: answer => {
                        // TODO: check if this used
                        // -> no flag is set to enable the confirmation dialog,
                        // we only display a message, unlike `confirm_start`
                        if (answer == "yes") {
                            // Reuse data from unload_all
                            const scan_data = this.state_get_data("unload_all");
                            this.state.on_scan(scan_data.location_barcode, true);
                        } else {
                            this.state_to("scan_destination");
                        }
                    },
                    on_scan: (scanned, confirmation = true) => {
                        this.on_state_exit();
                        // FIXME: use state_load or traverse the state
                        // this.current_state_key = "unload_all";
                        // this.state.on_scan(scanned, confirmation);
                        this.states["unload_all"].on_scan(scanned, confirmation);
                    },
                },
                unload_single: {
                    display_info: {
                        title: "Unload single bin",
                        scan_placeholder: "Scan location",
                    },
                    on_scan: scanned => {
                        this.wait_call(
                            this.odoo.call("unload_scan_pack", {
                                picking_batch_id: this.current_batch().id,
                                package_id: null, // FIXME: where does it come from? backend data?
                                barcode: scanned.text,
                            })
                        );
                    },
                },
                unload_set_destination: {
                    display_info: {
                        title: "Set destination",
                        scan_placeholder: "Scan location",
                    },
                    on_scan: scanned => {
                        this.wait_call(
                            this.odoo.call("unload_scan_destination", {
                                picking_batch_id: this.current_batch().id,
                                package_id: null, // FIXME: where does it come from? backend data?
                                barcode: scanned.text,
                            })
                        );
                    },
                },
                confirm_unload_set_destination: {
                    display_info: {
                        title: "Set destination confirm",
                        scan_placeholder: "Scan location",
                    },
                    on_scan: scanned => {
                        this.wait_call(
                            this.odoo.call("unload_scan_destination", {
                                picking_batch_id: this.current_batch().id,
                                package_id: null, // FIXME: where does it come from? backend data?
                                barcode: scanned.text,
                                confirmation: true,
                            })
                        );
                    },
                },
            },
        };
    },
};

process_registry.add("cluster_batch_picking", ClusterBatchPicking);

export default ClusterBatchPicking;
