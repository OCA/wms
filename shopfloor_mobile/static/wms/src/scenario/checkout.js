import {GenericStatesMixin, ScenarioBaseMixin} from "./mixins.js";
import {process_registry} from "../services/process_registry.js";
import {demotools} from "../demo/demo.core.js";

export var Checkout = Vue.component("checkout", {
    mixins: [ScenarioBaseMixin, GenericStatesMixin],
    template: `
        <Screen :title="screen_info.title" :klass="screen_info.klass">
            <!-- FOR DEBUG -->
            <!-- {{ current_state_key }} -->
            <template v-slot:header>
                <user-information
                    v-if="!need_confirmation && user_notification.message"
                    v-bind:info="user_notification"
                    />
                <state-display-info :info="state.display_info" v-if="state.display_info"/>
            </template>
            <searchbar
                v-if="state_in(['select_document', 'select_line'])"
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
                <checkout-picking-detail
                    :info="state.data"
                    :grouped_lines="group_lines_by_location(state.data.move_lines)"
                    v-on:select="state.on_select"
                    v-on:back="state.on_back"
                    />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn depressed color="primary" @click="state.on_summary">Summary</v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>

            <div v-if="state_is('summary')">
                <checkout-summary-detail
                    :info="state.data"
                    :grouped_lines="group_lines_by_location(state.data.move_lines, {'group_key': 'location_dest', 'prepare_records': group_by_pack})"
                    v-on:select="state.on_select"
                    v-on:back="state.on_back"
                    />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn depressed color="primary" @click="$emit('action', 'TODO')">TODO</v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>
            <div v-if="state_is('manual_selection')">
                <manual-select
                    v-on:select="state.on_select"
                    v-on:back="state.on_back"
                    :records="state.data.records"
                    :list_item_fields="manual_select_picking_fields"
                    />
            </div>
        </Screen>
        `,
    computed: {
        picking_id: function() {
            return this.erp_data.data.select_line.id;
        },
        manual_select_picking_fields: function() {
            return [
                {path: "partner.name"},
                {path: "origin"},
                {path: "move_line_count", label: "Lines"},
            ];
        },
    },
    // Mounted: function () {
    //     // FIXME: just for dev
    //     this.initial_state_key = 'summary'
    //     this.set_erp_data('data', {
    //         'summary': demotools.makePicking({}, {"lines_count": 5, "line_random_pack": true}),
    //     });
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
                    key: pack ? pack.name : "no-pack",
                    // No pack, just display the product name
                    title: pack ? pack.name : products[0].display_name,
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
            const pkgs = _.uniqBy(
                _.map(lines, function(x) {
                    return x.package_dest ? x.package_dest.package_name : null;
                }),
                "id"
            );
            const grouped = _.groupBy(lines, "package_dest.package_name");
            _.forEach(grouped, function(products, package_name) {
                const pkg = _.first(_.filter(pkgs, {package_name: package_name}));
                res.push({
                    key: pkg ? pkg.name : "no-pkg",
                    // No pack, just display the product name
                    title: pkg ? pkg.name : "NO-PKG",
                    records: products,
                });
            });
            return res;
        },
    },
    data: function() {
        return {
            usage: "checkout",
            // 'initial_state_key': 'summary',
            initial_state_key: "select_document",
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
                        const line = selected[0];
                        console.log("SELECTED", line);
                        this.go_state(
                            "wait_call",
                            this.odoo.call("select_line", {
                                picking_id: this.picking_id,
                                move_line_id: line.id,
                                package_id: _.result(line, "package_dest.id", null),
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
                    on_action: action => {
                        this.state["on_" + action].call(this);
                    },
                    on_select_line: () => {
                        throw "NOT IMPLEMENTED";
                        this.go_state(
                            "wait_call",
                            this.odoo.call("set_line_qty", {
                                move_line_id: this.state.data.id,
                            })
                        );
                    },
                    on_new_pack: () => {
                        throw "NOT IMPLEMENTED";
                    },
                    on_existing_pack: () => {
                        throw "NOT IMPLEMENTED";
                    },
                    on_without_pack: () => {
                        throw "NOT IMPLEMENTED";
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
                        this.go_state(
                            "wait_call",
                            this.odoo.call("scan_dest_package", {
                                barcode: scanned.text,
                            })
                        );
                    },
                    on_action: action => {
                        this.state["on_" + action].call(this);
                    },
                    on_set_package: pkg => {
                        throw "NOT IMPLEMENTED";
                        this.go_state(
                            "wait_call",
                            this.odoo.call("set_dest_package", {
                                move_line_id: this.state.data.id,
                                package_id: pkg.id,
                            })
                        );
                    },
                },
                summary: {
                    display_info: {
                        title: "Summary",
                    },
                    on_select: selected => {
                        if (!selected) {
                            return;
                        }
                        console.log("ON SELECT - TODO");
                    },
                    on_back: () => {
                        this.go_state("start");
                        this.reset_notification();
                    },
                    on_action: action => {
                        this.state["on_" + action].call(this);
                    },
                    on_pkg_change_type: pkg => {
                        throw "NOT IMPLEMENTED";
                    },
                    on_pkg_destroy: pkg => {
                        throw "NOT IMPLEMENTED";
                    },
                    on_mark_as_done: pkg => {
                        throw "NOT IMPLEMENTED";
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
