import {ScenarioBaseMixin} from "./mixins.js";
import {process_registry} from "../services/process_registry.js";
import {utils} from "../utils.js";
import {demotools} from "../demo/demo.core.js"; // FIXME: dev only
import {} from "../demo/demo.checkout.js"; // FIXME: dev only

export var Checkout = Vue.component("checkout", {
    mixins: [ScenarioBaseMixin],
    /*
        /!\ IMPORTANT: we use many times the same component
        (eg: manual-select or detail-picking-select)
        and to make sure they don't get cached together
        we MUST call them using `:key` to make them unique!
        If you don't, you'll have severe problems of data being shared
        between each instances. This is the real problem:
        you assume to have different instance but indeed you get only 1
        which is reused every time!
    */
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
            <div v-if="state_is('select_document')">
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn depressed color="primary" @click="state.on_manual_selection">Manual selection</v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>
            <div v-if="state_is('manual_selection')">
                <manual-select
                    :records="state.data.pickings"
                    :list_item_fields="manual_select_picking_fields"
                    :key="current_state_key + '-manual-select'"
                    />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn depressed color="default" @click="state.on_back">Back</v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>
            <div v-if="state_is('select_line')">
                <detail-picking-select
                    :picking="state.data.picking"
                    :select_records="state.data.picking.move_lines"
                    :select_records_grouped="utils.group_lines_by_location(state.data.picking.move_lines, {'prepare_records': utils.only_one_package})"
                    :key="current_state_key + '-detail-picking-select'"
                    />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn depressed color="primary" @click="$root.trigger('summary')">Summary</v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>

            <div v-if="state_is('select_package')">
                <detail-picking-select
                    :picking="state.data.picking"
                    :select_records="state.data.selected_move_lines"
                    :select_options="{multiple: true, initSelectAll: true, list_item_component: 'picking-select-package-content'}"
                    :key="current_state_key + '-detail-picking-select'"
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
                <picking-summary
                    :picking="state.data.picking"
                    :records_grouped="utils.group_lines_by_location(state.data.picking.move_lines, {'group_key': 'location_dest', 'prepare_records': utils.group_by_pack})"
                    :list_options="{list_item_options: {actions: ['action_change_pkg', 'action_cancel_line']}}"
                    :key="current_state_key + '-picking-summary'"
                    />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn depressed color="primary" @click="$root.trigger('mark_as_done')"
                                   :disabled="state.data.picking.move_lines.length < 1">Mark as done</v-btn>
                        </v-col>
                    </v-row>
                    <v-row align="center" v-if="!state.data.all_processed">
                        <v-col class="text-center" cols="12">
                            <v-btn depressed color="primary" @click="$root.trigger('continue')">Continue checkout</v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>
            <div v-if="state_is('select_dest_package')">
                <detail-picking-select
                    :picking="state.data.picking"
                    :select_records="state.data.packages"
                    :select_options="{list_item_fields: existing_package_select_fields, list_item_component: 'list-item'}"
                    :key="current_state_key + '-detail-picking-select'"
                    />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-back />
                        </v-col>
                    </v-row>
                </div>
            </div>
            <div v-if="state_is('change_quantity')">
                <detail-picking :picking="state.data.picking" />
                <div class="qty">
                    <input-number-spinner
                        v-on:input="state.on_qty_update"
                        :init_value="state.data.record.qty_done"
                        class="mb-2"
                        />
                </div>
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn depressed color="primary" @click="$root.trigger('qty_change_confirm')">Confirm</v-btn>
                        </v-col>
                    </v-row>
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn depressed color="default" @click="state.on_back">Back</v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>
            <div v-if="state_is('change_packaging')">
                <detail-picking-select
                    :picking="state.data.picking"
                    :select_records="state.data.packagings"
                    :select_options="{list_item_component: 'list-item'}"
                    :key="current_state_key + '-detail-picking-select'"
                    />
            </div>
            <div v-if="state_is('confirm_done')">
                <detail-picking :picking="state.data.picking" />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn depressed color="success" @click="state.on_confirm">Confirm</v-btn>
                        </v-col>
                    </v-row>
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn depressed color="default" @click="state.on_back">Back</v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>
        </Screen>
        `,
    computed: {
        utils: function() {
            return utils;
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
                {path: "packaging.name"},
            ];
        },
    },
    // FIXME: just for dev
    // mounted: function() {
    //     // TEST force state and data
    //     const state = "select_package";
    //     const dcase = demotools.get_case(this.usage);
    //     const data = dcase["select_package"].data[state];
    //     this.state_set_data(data, state);
    //     this._state_load(state);
    // },
    methods: {
        record_by_id: function(records, _id) {
            // TODO: double check when the process is done if this is still needed or not.
            // `manual-select` can now buble up events w/ full record.
            return _.first(_.filter(records, {id: _id}));
        },
    },
    data: function() {
        return {
            usage: "checkout",
            initial_state_key: "select_document",
            states: {
                select_document: {
                    display_info: {
                        title: "Choose an order to pack",
                        scan_placeholder: "Scan pack / picking / location",
                    },
                    enter: () => {
                        this.state_reset_data();
                    },
                    on_scan: scanned => {
                        this.wait_call(
                            this.odoo.call("scan_document", {barcode: scanned.text})
                        );
                    },
                    on_manual_selection: evt => {
                        this.wait_call(this.odoo.call("list_stock_picking"));
                    },
                },
                manual_selection: {
                    display_info: {
                        title: "Select a picking and start",
                    },
                    events: {
                        select: "on_select",
                    },
                    on_back: () => {
                        this.state_to("start");
                        this.reset_notification();
                    },
                    on_select: selected => {
                        this.wait_call(
                            this.odoo.call("select", {
                                picking_id: selected.id,
                            })
                        );
                    },
                },
                select_line: {
                    display_info: {
                        title: "Pick the product by scanning something",
                        scan_placeholder: "Scan pack / product / lot",
                    },
                    events: {
                        summary: "on_summary",
                        select: "on_select",
                        back: "on_back",
                    },
                    on_scan: scanned => {
                        this.wait_call(
                            this.odoo.call("scan_line", {
                                picking_id: this.state.data.picking.id,
                                barcode: scanned.text,
                            })
                        );
                    },
                    on_select: selected => {
                        if (!selected) {
                            return;
                        }
                        this.wait_call(
                            this.odoo.call("select_line", {
                                picking_id: this.state.data.picking.id,
                                move_line_id: selected.id,
                                package_id: _.result(
                                    selected,
                                    "package_dest.id",
                                    false
                                ),
                            })
                        );
                    },
                    on_back: () => {
                        this.state_to("start");
                        this.reset_notification();
                    },
                    on_summary: () => {
                        this.wait_call(
                            this.odoo.call("summary", {
                                picking_id: this.state.data.picking.id,
                            })
                        );
                    },
                    // FIXME: is not to change qty
                    on_edit_package: pkg => {
                        this.state_set_data({package: pkg}, change_quantity);
                        this.state_to("change_quantity");
                    },
                },
                select_package: {
                    // TODO: /set_line_qty is not handled yet
                    // because is not clear how to handle line selection
                    // and qty set.
                    // ATM given that manual-select uses v-list-item-group
                    // when you touch a line you select/unselect it
                    // which means we cannot rely on this to go to edit.
                    // If we need it, we have to change manual-select
                    // to use pure list + checkboxes.
                    display_info: {
                        title: "Select package",
                        scan_placeholder: "Scan existing package / package type",
                    },
                    events: {
                        qty_edit: "on_qty_edit",
                        select: "on_select",
                        back: "on_back",
                    },
                    enter: () => {
                        this.state_set_data({
                            selected: this.state.data.selected_move_lines,
                        });
                    },
                    on_scan: scanned => {
                        this.wait_call(
                            this.odoo.call("scan_package_action", {
                                picking_id: this.state.data.picking.id,
                                selected_line_ids: _.map(
                                    this.state.data.selected,
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
                        // keep selected lines on the state
                        this.state_set_data({selected: selected});
                        // Must pick unselected line and reset its qty
                        const unselected = _.head(
                            _.difference(this.state.data.selected_move_lines, selected)
                        );
                        if (unselected) {
                            console.log("unselected", unselected);
                            this.wait_call(
                                this.odoo.call("reset_line_qty", {
                                    move_line_id: unselected.id,
                                })
                            );
                        }
                    },
                    on_qty_edit: record => {
                        this.state_set_data(
                            {
                                picking: this.state.data.picking,
                                record: record,
                                selected_line_ids: _.map(
                                    this.state.data.selected,
                                    _.property("id")
                                ),
                            },
                            "change_quantity"
                        );
                        this.state_to("change_quantity");
                    },
                    on_new_pack: () => {
                        this.wait_call(
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
                        this.wait_call(
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
                        this.wait_call(
                            this.odoo.call("no_package", {
                                picking_id: this.state.data.picking.id,
                                selected_line_ids: _.map(
                                    this.state.data.selected,
                                    _.property("id")
                                ),
                            })
                        );
                    },
                    on_back: () => {
                        this.state_to("select_line");
                        this.reset_notification();
                    },
                },
                change_quantity: {
                    display_info: {
                        title: "Change quantity",
                    },
                    events: {
                        qty_change_confirm: "on_confirm",
                    },
                    on_back: () => {
                        this.state_to("select_package");
                        this.reset_notification();
                    },
                    on_qty_update: qty => {
                        console.log(qty);
                        this.state.data.qty = qty;
                    },
                    on_confirm: () => {
                        this.wait_call(
                            this.odoo.call("set_custom_qty", {
                                picking_id: this.state.data.picking.id,
                                selected_line_ids: this.state.data.selected_line_ids,
                                move_line_id: this.state.data.record.id,
                                qty_done: this.state.data.qty,
                            })
                        );
                    },
                },
                select_dest_package: {
                    display_info: {
                        title: "Select destination package",
                    },
                    events: {
                        select: "on_select",
                        back: "on_back",
                    },
                    on_scan: scanned => {
                        const selected_lines = this.state_get_data("select_package")
                            .selected;
                        this.wait_call(
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
                        const selected_lines = this.state_get_data("select_package")
                            .selected;
                        this.wait_call(
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
                        this.state_to("select_package");
                        this.reset_notification();
                    },
                },
                summary: {
                    display_info: {
                        title: "Summary",
                    },
                    events: {
                        select: "on_select",
                        back: "on_back",
                        cancel_picking_line: "on_cancel",
                        pkg_change_type: "on_pkg_change_type",
                        mark_as_done: "on_mark_as_done",
                        continue: "on_continue",
                    },
                    on_back: () => {
                        this.state_to("start");
                        this.reset_notification();
                    },
                    on_pkg_change_type: pkg => {
                        this.wait_call(
                            this.odoo.call("list_packaging", {
                                picking_id: this.state.data.picking.id,
                                package_id: pkg.id,
                            })
                        );
                    },
                    on_cancel: data => {
                        this.wait_call(
                            this.odoo.call("cancel_line", {
                                picking_id: this.state.data.picking.id,
                                // we get either line_id or package_id
                                package_id: data.package_id,
                                line_id: data.line_id,
                            })
                        );
                    },
                    on_mark_as_done: () => {
                        this.wait_call(
                            this.odoo.call("done", {
                                picking_id: this.state.data.picking.id,
                            })
                        );
                    },
                    on_continue: () => {
                        this.wait_call(
                            this.odoo.call("select", {
                                picking_id: this.state.data.picking.id,
                            })
                        );
                    },
                },
                change_packaging: {
                    display_info: {
                        title: "Change packaging",
                    },
                    events: {
                        select: "on_select",
                        back: "on_back",
                    },
                    on_select: selected => {
                        if (!selected) {
                            return;
                        }
                        this.wait_call(
                            this.odoo.call("set_packaging", {
                                picking_id: this.state.data.picking.id,
                                pickage_id: this.state.data.package.id,
                                packaging_id: selected.id,
                            })
                        );
                    },
                    on_back: () => {
                        this.state_to("start");
                        this.reset_notification();
                    },
                },
                confirm_done: {
                    display_info: {
                        title: "Confirm done",
                    },
                    on_confirm: () => {
                        this.wait_call(
                            this.odoo.call("done", {
                                picking_id: this.state.data.picking.id,
                                confirmation: true,
                            })
                        );
                    },
                    on_back: () => {
                        this.state_to("summary");
                        this.reset_notification();
                    },
                },
            },
        };
    },
});

process_registry.add("checkout", Checkout);
