import {GenericStatesMixin, ScenarioBaseMixin} from "./mixins.js";
import {process_registry} from "../services/process_registry.js";
import {demotools} from "../demo/demo.core.js"; // FIXME: dev only
import {} from "../demo/demo.checkout.js"; // FIXME: dev only

export var Checkout = Vue.component("checkout", {
    mixins: [ScenarioBaseMixin, GenericStatesMixin],
    template: `
        <Screen :title="screen_info.title" :klass="screen_info.klass">
            <!-- FOR DEBUG -->
            {{ current_state_key }}
            <template v-slot:header>
                <user-information
                    v-if="!need_confirmation && user_notification.message"
                    v-bind:info="user_notification"
                    />
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
                            <v-btn depressed color="primary" @click="state.on_manual_selection">Manual selection</v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>

            <div v-if="state_is('select_line')">
                <checkout-picking-detail-select
                    :picking="state.data"
                    :select_records="state.data.move_lines"
                    :select_records_grouped="group_lines_by_location(state.data.move_lines)"
                    :select_options="{bubbleUpAction: true}"
                    v-on:select="on_select"
                    v-on:back="on_back"
                    />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn depressed color="primary" @click="$root.trigger('summary')">Summary</v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>

            <div v-if="state_is('select_pack')">
                <checkout-picking-detail-select
                    :picking="state.data.picking"
                    :select_records="state.data.selected_move_lines"
                    :select_options="{multiple: true, initSelectAll: true, bubbleUpAction: true, list_item_component: 'checkout-select-package-content'}"
                    v-on:select="on_select"
                    v-on:back="on_back"
                    />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn depressed color="primary"
                                   @click="state.on_existing_pack"
                                   :disabled="state.data.selected && !state.data.selected.length"
                                   >Existing pack</v-btn>
                        </v-col>
                    </v-row>
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn depressed color="primary"
                                   @click="state.on_new_pack"
                                   :disabled="state.data.selected && !state.data.selected.length"
                                   >New pack</v-btn>
                        </v-col>
                    </v-row>
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn depressed color="primary"
                                   @click="state.on_without_pack"
                                   :disabled="state.data.selected && !state.data.selected.length"
                                   >Process w/o pack</v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>

            <div v-if="state_is('summary')">
                <checkout-summary-detail
                    :picking="state.data.picking"
                    :select_records_grouped="group_lines_by_location(state.data.picking.move_lines, {'group_key': 'location_dest', 'prepare_records': group_by_pack})"
                    :select_options="{showActions: false}"
                    v-on:select="on_select"
                    v-on:back="on_back"
                    />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn depressed color="primary" @click="$root.trigger('mark_as_done')">Mark as done</v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>
            <div v-if="state_is('manual_selection')">
                <manual-select
                    v-on:select="on_select"
                    v-on:back="on_back"
                    :records="state.data.records"
                    :list_item_fields="manual_select_picking_fields"
                    />
            </div>
            <div v-if="state_is('select_dest_package')">
                <checkout-picking-detail-select
                    :info="state.data.picking"
                    :select_records="state.data.packages"
                    :select_options="{bubbleUpAction: true, list_item_fields: existing_package_select_fields, list_item_component: 'manual-select-item'}"
                    v-on:select="on_select"
                    v-on:back="on_back"
                    />
            </div>
        </Screen>
        `,
    computed: {
        picking_id: function() {
            return this.erp_data.data.select_line.id;
        },
        // TODO: move these to methods
        manual_select_picking_fields: function() {
            return [
                {path: "partner.name"},
                {path: "origin"},
                {path: "move_line_count", label: "Lines"},
            ];
        },
        existing_package_select_fields: function() {
            return [
                {path: "weight"},
                {path: "move_line_count", label: "Line count"},
                {path: "packaging_name"},
            ];
        },
    },
    // FIXME: just for dev
    // Mmounted: function () {
    //     // TEST summary only
    //     // this.initial_state_key = 'summary'
    //     // this.set_erp_data('data', {
    //     //     'summary': demotools.makePicking({}, {"lines_count": 5, "line_random_pack": true}),
    //     // });
    //     // TEST select_pack only
    //     this.initial_state_key = 'select_pack'
    //     this.set_erp_data('data', demotools.get_case(this.usage).select_line.data);
    //     // this.initial_state_key = 'select_dest_package'
    //     // this.set_erp_data('data', demotools.get_case(this.usage).select_line.data);
    // },
    methods: {
        record_by_id: function(records, _id) {
            // TODO: double check when the process is done if this is still needed or not.
            // `manual-select` can now buble up events w/ full record.
            return _.first(_.filter(records, {id: _id}));
        },
        group_lines_by_location: function(lines, options) {
            // {'key': 'no-group', 'title': '', 'records': []}
            options = _.defaults(options || {}, {
                group_key: "location_src",
                name_prefix: "Location",
                prepare_records: function(recs) {
                    return recs;
                },
            });
            const res = [];
            const locations = _.uniqBy(
                _.map(lines, function(x) {
                    return x[options.group_key];
                }),
                "id"
            );
            const grouped = _.groupBy(lines, options.group_key + ".id");
            _.forEach(grouped, function(value, loc_id) {
                const location = _.first(_.filter(locations, {id: parseInt(loc_id)}));
                const title = options.name_prefix
                    ? options.name_prefix + ": " + location.name
                    : location.name;
                res.push({
                    key: loc_id,
                    title: title,
                    records: options.prepare_records(value),
                });
            });
            return res;
        },
        group_by_pack: function(lines) {
            const self = this;
            const res = [];
            const packs = _.uniqBy(
                _.map(lines, function(x) {
                    return x.package_dest;
                }),
                "id"
            );
            const grouped = _.groupBy(lines, "package_dest.id");
            _.forEach(grouped, function(products, pack_id) {
                const pack = _.first(_.filter(packs, {id: parseInt(pack_id)}));
                res.push({
                    key: pack ? pack_id : "no-pack",
                    // No pack, just display the product name
                    title: pack ? pack.name : products[0].display_name,
                    pack: pack,
                    records: products,
                    records_by_pkg_type: pack
                        ? self.group_by_package_type(products)
                        : null,
                });
            });
            return res;
        },
        group_by_package_type: function(lines) {
            const res = [];
            const grouped = _.groupBy(lines, "package_dest.packaging_name");
            _.forEach(grouped, function(products, packaging_name) {
                res.push({
                    key: packaging_name,
                    title: packaging_name,
                    records: products,
                });
            });
            return res;
        },
    },
    data: function() {
        return {
            usage: "checkout",
            // initial_state_key: "select_document",
            initial_state_key: "select_pack", // FIXME: just for dev
            // initial_state_key: "select_dest_package",  // FIXME: just for dev
            states: {
                select_document: {
                    display_info: {
                        title: "Start by scanning something",
                        scan_placeholder: "Scan pack / picking / location",
                    },
                    enter: () => {
                        this.reset_erp_data("data");
                    },
                    on_scan: scanned => {
                        this.go_state(
                            "wait_call",
                            this.odoo.call("scan_document", {barcode: scanned.text})
                        );
                    },
                    on_manual_selection: evt => {
                        this.go_state(
                            "wait_call",
                            this.odoo.call("list_stock_picking")
                        );
                    },
                },
                manual_selection: {
                    on_back: () => {
                        this.go_state("start");
                        this.reset_notification();
                    },
                    on_select: selected => {
                        this.go_state(
                            "wait_call",
                            this.odoo.call("select", {
                                picking_id: selected,
                            })
                        );
                    },
                    display_info: {
                        title: "Select a picking and start",
                    },
                },
                select_line: {
                    display_info: {
                        title: "Pick the product by scanning something",
                        scan_placeholder: "Scan pack / product / lot",
                    },
                    on_scan: scanned => {
                        this.go_state(
                            "wait_call",
                            this.odoo.call("scan_line", {
                                picking_id: this.picking_id,
                                barcode: scanned.text,
                            })
                        );
                    },
                    on_select: selected => {
                        if (!selected) {
                            return;
                        }
                        this.go_state(
                            "wait_call",
                            this.odoo.call("select_line", {
                                picking_id: this.picking_id,
                                move_line_id: selected.id,
                                package_id: _.result(selected, "package_dest.id", null),
                            })
                        );
                    },
                    on_back: () => {
                        this.go_state("start");
                        this.reset_notification();
                    },
                    on_summary: () => {
                        this.go_state(
                            "wait_call",
                            this.odoo.call("summary", {
                                picking_id: this.picking_id,
                            })
                        );
                    },
                },
                select_pack: {
                    display_info: {
                        title: "Select pack",
                    },
                    on_qty_update: qty => {
                        this.scan_destination_qty = parseInt(qty);
                    },
                    on_scan: scanned => {
                        this.go_state(
                            "wait_call",
                            this.odoo.call("scan_pack_action", {
                                move_line_id: this.state.data.id,
                                barcode: scanned.text,
                                quantity: this.scan_destination_qty,
                            })
                        );
                    },
                    on_select: selected => {
                        if (!selected) {
                            return;
                        }
                        // keep selected lines on the state
                        this.state.data.selected = selected;
                        // Must pick unselected line and reset its qty
                        const unselected = _.head(
                            _.difference(this.state.data.selected_move_lines, selected)
                        );
                        if (unselected) {
                            console.log("unselected", unselected);
                            this.go_state(
                                "wait_call",
                                this.odoo.call("reset_line_qty", {
                                    move_line_id: unselected.id,
                                })
                            );
                        }
                    },
                    on_new_pack: () => {
                        this.go_state(
                            "wait_call",
                            this.odoo.call("new_package", {
                                picking_id: this.state.data.picking.id,
                                selected_line_ids: _.map(
                                    this.state.data.selected,
                                    _.property("id")
                                ),
                            })
                        );
                    },
                    on_existing_pack: () => {
                        this.go_state(
                            "wait_call",
                            this.odoo.call("list_dest_package", {
                                picking_id: this.state.data.picking.id,
                                selected_line_ids: _.map(
                                    this.state.data.selected,
                                    _.property("id")
                                ),
                            })
                        );
                    },
                    on_without_pack: () => {
                        this.set_notification({
                            message_type: "info",
                            message: "Product(s) processed as raw product(s)",
                        });
                        this.go_state("select_line");
                    },
                    on_back: () => {
                        this.go_state("select_line");
                        this.reset_notification();
                    },
                },
                change_qty: {
                    display_info: {
                        title: "Change quantity",
                    },
                    on_qty_update: qty => {
                        this.state.data.qty = parseInt(qty);
                    },
                    on_action: action => {
                        this.state["on_" + action].call(this);
                    },
                    on_change_qty: () => {
                        throw "NOT IMPLEMENTED";
                        this.go_state(
                            "wait_call",
                            this.odoo.call("set_custom_qty", {
                                move_line_id: this.state.data.id,
                                quantity: this.state.data.qty,
                            })
                        );
                    },
                },
                select_dest_package: {
                    display_info: {
                        title: "Select destination package",
                    },
                    on_scan: scanned => {
                        const selected_lines = this.state_get_data("select_pack")
                            .selected;
                        this.go_state(
                            "wait_call",
                            this.odoo.call("scan_dest_package", {
                                picking_id: this.state.data.picking.id,
                                selected_line_ids: _.map(
                                    selected_lines,
                                    _.property("id")
                                ),
                                barcode: scanned.text,
                            })
                        );
                    },
                    on_select: selected => {
                        if (!selected) {
                            return;
                        }
                        const selected_lines = this.state_get_data("select_pack")
                            .selected;
                        this.go_state(
                            "wait_call",
                            this.odoo.call("set_dest_package", {
                                picking_id: this.state.data.picking.id,
                                selected_line_ids: _.map(
                                    selected_lines,
                                    _.property("id")
                                ),
                                package_id: selected.id,
                            })
                        );
                    },
                    on_back: () => {
                        this.go_state("select_pack");
                        this.reset_notification();
                    },
                },
                summary: {
                    display_info: {
                        title: "Summary",
                    },
                    events: {
                        pkg_destroy: "on_pkg_destroy",
                        pkg_change_type: "on_pkg_change_type",
                        mark_as_done: "on_mark_as_done",
                    },
                    on_select: selected => {
                        if (!selected) {
                            return;
                        }
                        this.state.data.selected = selected;
                    },
                    on_back: () => {
                        this.go_state("start");
                        this.reset_notification();
                    },
                    on_pkg_change_type: pkg => {
                        throw "NOT IMPLEMENTED";
                    },
                    on_pkg_destroy: pkg => {
                        this.odoo.call("remove_package", {
                            picking_id: this.state.data.picking.id,
                            package_id: pkg.id,
                        });
                    },
                    on_mark_as_done: () => {
                        this.odoo.call("done", {
                            picking_id: this.state.data.picking.id,
                        });
                    },
                },
                change_package_type: {
                    display_info: {
                        title: "Change package type",
                    },
                    on_action: action => {
                        this.state["on_" + action].call(this);
                    },
                    on_do_it: pkg => {
                        throw "NOT IMPLEMENTED";
                    },
                },
            },
        };
    },
});

process_registry.add("checkout", Checkout);
