/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ScenarioBaseMixin} from "/shopfloor_mobile_base/static/wms/src/scenario/mixins.js";
import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

const template_mobile = `
    <Screen :screen_info="screen_info">
        <template v-slot:header>
            <state-display-info :info="state.display_info" v-if="state.display_info"/>
        </template>
        <searchbar
            v-if="state.on_scan"
            v-on:found="on_scan"
            :input_placeholder="search_input_placeholder"
            />

        <div v-if="state_is('scan_location')">
            <manual-select
                v-on:select="state.on_select"
                :records="state.data.zones"
                :options="scan_location_manual_select_options()"
                :key="make_state_component_key(['manual-select'])"
                />
            <div class="button-list button-vertical-list full">
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <btn-back :router_back="false"/>
                    </v-col>
                </v-row>
            </div>
        </div>
        <div v-if="state_is('select_picking_type')">
            <manual-select
                v-on:select="state.on_select"
                :records="state.data.picking_types"
                :options="select_picking_type_manual_select_options()"
                :key="make_state_component_key(['manual-select'])"
                />
            <div class="button-list button-vertical-list full">
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <btn-back :router_back="false"/>
                    </v-col>
                </v-row>
            </div>
        </div>

        <div v-if="state_is('select_line')">
            <manual-select
                v-if="device_mode == 'mobile'"
                :records="state.data.move_lines"
                :options="select_line_move_line_detail_options()"
                :key="make_state_component_key(['manual-select'])"
                />

            <v-data-table
                v-if="device_mode == 'desktop'"
                :headers="select_line_table_headers()"
                :items="select_line_table_items()"
                :key="make_state_component_key(['data-table'])"
                class="elevation-1">

                <template v-slot:item.quantity="{ item }">
                    <packaging-qty-picker-display
                        :key="make_state_component_key(['qty-picker-widget', item['_origin'].id])"
                        :options="utils.wms.move_line_qty_picker_options(item['_origin'])"
                        />
                </template>
                <template v-slot:item.priority="{ item }">
                    <priority-widget
                        :key="make_state_component_key(['priority-widget', item['_origin'].id])"
                        :options="{priority: parseInt(item.priority || '0', 10)}" />
                </template>
                <template v-slot:item.location_will_be_empty="{ item }">
                    <empty-location-icon :record="item"
                        :key="make_state_component_key(['empty-location-icon', item['_origin'].id])"
                        />
                </template>
            </v-data-table>

            <div class="button-list button-vertical-list full">
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <btn-action @click="toggle_sort_lines_by()">{{ sort_lines_by_btn_label }}</btn-action>
                    </v-col>
                </v-row>
                <!-- TODO: this btn should be available only if there are lines already processed -->
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <btn-action @click="state.on_unload_at_destination()">Unload at destination</btn-action>
                    </v-col>
                </v-row>
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <btn-back :router_back="false"/>
                    </v-col>
                </v-row>
            </div>
        </div>

        <detail-picking
            v-if="state_is('set_line_destination')"
            :record="state.data.move_line.picking"
            :card_color="utils.colors.color_for('screen_step_done')"
            />
        <item-detail-card
            v-if="state_in(['set_line_destination', 'change_pack_lot'])"
            :key="make_state_component_key(['detail-move-line-loc', state.data.move_line.id])"
            :record="state.data.move_line"
            :options="{main: true, key_title: 'location_src.name', title_action_field: {action_val_path: 'location_src.barcode'}}"
            :card_color="utils.colors.color_for('screen_step_done')"
            />
        <item-detail-card
            v-if="state_in(['set_line_destination', 'stock_issue', 'change_pack_lot'])"
            :key="make_state_component_key(['detail-move-line-product', state.data.move_line.id])"
            :record="state.data.move_line"
            :options="utils.wms.move_line_product_detail_options(state.data.move_line, {fields: [{path: 'picking.name', label: 'Picking'}], fields_blacklist: ['quantity']})"
            :card_color="utils.colors.color_for(state_in(['set_line_destination']) ? 'screen_step_done': 'screen_step_todo')"
            />
        <item-detail-card
            v-if="state_in(['set_line_destination'])"
            :key="make_state_component_key(['detail-move-line-loc-dest', state.data.move_line.id])"
            :record="state.data.move_line"
            :options="{main: true, key_title: 'location_dest.name', title_action_field: {action_val_path: 'location_dest.barcode'}}"
            :card_color="utils.colors.color_for('screen_step_todo')"
            />
        <v-card v-if="state_in(['set_line_destination', 'change_pack_lot'])"
                class="pa-2" :color="utils.colors.color_for('screen_step_todo')">
            <packaging-qty-picker
                :key="make_state_component_key(['packaging-qty-picker', state.data.move_line.id])"
                :options="utils.wms.move_line_qty_picker_options(state.data.move_line)"
                />
        </v-card>
        <item-detail-card
            v-if="state_in(['change_pack_lot'])"
            :key="make_state_component_key(['detail-move-line-dest-pack', state.data.move_line.id])"
            :record="state.data.move_line"
            :options="{main: true, key_title: 'package_dest.name'}"
            :card_color="utils.colors.color_for('screen_step_todo')"
            />
        <div v-if="state_is('set_line_destination')">
            <line-actions-popup
                :line="state.data.move_line"
                :actions="[
                    {name: 'Declare stock out', event_name: 'action_stock_out'},
                    {name: 'Change pack or lot', event_name: 'action_change_pack_lot'},
                ]"
                :key="make_state_component_key(['line-actions', state.data.move_line.id])"
                v-on:action="state.on_action"
                />
        </div>

        <div v-if="state_in(['unload_all'])">
            <picking-summary
                :record="state.data.move_lines[0].picking"
                :records="state.data.move_lines"
                :records_grouped="picking_summary_records_grouped(state.data.move_lines)"
                :list_options="picking_summary_move_line_list_options(state.data.move_lines)"
                :key="make_state_component_key(['picking-summary'])"
                />
            <div class="button-list button-vertical-list full">
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <btn-action @click="state.on_action_split()">Split</btn-action>
                    </v-col>
                </v-row>
            </div>
        </div>

        <div v-if="state_in(['unload_single', 'unload_set_destination'])">
            <user-information
                v-if="state.data.full_order_picking"
                :message="{body: 'Full order picking, no more operation.'}"
                />
            <picking-summary
                v-if="state.data.move_line"
                :record="state.data.move_line.picking"
                :records="[state.data.move_line]"
                :records_grouped="picking_summary_records_grouped([state.data.move_line])"
                :list_options="picking_summary_move_line_list_options([state.data.move_line])"
                :key="make_state_component_key(['picking-summary'])"
                />
            <div class="no-line-found" v-if="_.isEmpty(state.data.move_line)">
                <!-- In theory this should not happen.
                Handled only because something seems wrong backend side
                and we might get here w/ no line info. -->
                No line to process.
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
        <div class="button-list button-vertical-list full">
            <v-row align="center" v-if="state_in(['change_pack_lot'])">
                <v-col class="text-center" cols="12">
                    <btn-back />
                </v-col>
            </v-row>
        </div>
    </Screen>
`;

const TEMPLATES = {
    mobile: Vue.compile(template_mobile),
    desktop: Vue.compile(template_mobile),
};

const ZonePicking = {
    mixins: [ScenarioBaseMixin],
    methods: {
        /**
         * Override to inject headers for zone location and picking type when needed.
         */
        _get_odoo_params: function() {
            const params = this.$super(ScenarioBaseMixin)._get_odoo_params();
            const zone = this.current_zone_location();
            const picking_type = this.current_picking_type();
            if (_.isUndefined(params.headers)) {
                params["headers"] = {};
            }
            _.defaults(
                params.headers,
                this._get_zone_picking_headers(zone.id, picking_type.id)
            );
            return params;
        },
        /**
         * Retrieve zone_picking scenario specific headers.
         *
         * The zone picking scenario requires some special headers
         * to share some key parameters accross all methods.
         *
         * @param {*} zone_id: ID of current zone
         * @param {*} picking_type_id: ID of selected picking type
         */
        _get_zone_picking_headers: function(zone_id, picking_type_id) {
            let res = {};
            if (_.isInteger(zone_id)) {
                res["SERVICE-CTX-ZONE-LOCATION-ID"] = zone_id;
            }
            if (_.isInteger(picking_type_id)) {
                res["SERVICE-CTX-PICKING-TYPE-ID"] = picking_type_id;
            }
            res["SERVICE-CTX-LINES-ORDER"] = this.order_lines_by;
            return res;
        },
        screen_klass: function() {
            return (
                this.$super(ScenarioBaseMixin).screen_klass() +
                " device-mode-" +
                this.device_mode
            );
        },
        screen_title: function() {
            const record = this.current_picking_type();
            if (!record) return this.menu_item().name;
            return record.name;
        },
        // TODO: if we have this working we can remove the picking detail?
        current_doc: function() {
            const record = this.current_picking_type();
            return {
                record: record,
            };
        },
        current_picking_type: function() {
            if (
                ["start", "scan_location", "select_picking_type"].includes(
                    this.current_state_key
                )
            ) {
                return {};
            }
            const data = this.state_get_data("select_line");
            if (_.isEmpty(data) || _.isEmpty(data.picking_type)) {
                return {};
            }
            return data.picking_type;
        },
        current_zone_location: function() {
            if (["start", "scan_location"].includes(this.current_state_key)) {
                return {};
            }
            const data = this.state_get_data("select_picking_type");
            if (_.isEmpty(data) || _.isEmpty(data.zone_location)) {
                return {};
            }
            return data.zone_location;
        },
        scan_location_manual_select_options: function() {
            return {
                group_title_default: "Available zones",
                group_color: this.utils.colors.color_for("screen_step_todo"),
                showActions: false,
                list_item_options: {
                    show_title: false,
                    fields: this.manual_select_zone_fields(),
                },
            };
        },
        manual_select_zone_fields: function() {
            return [
                {
                    path: "name",
                    render_component: "select-zone-item",
                },
            ];
        },
        select_picking_type_manual_select_options: function() {
            return {
                group_title_default: "Available operation types",
                group_color: this.utils.colors.color_for("screen_step_todo"),
                showActions: false,
                list_item_options: {
                    show_title: false,
                    fields: this.manual_select_picking_type_fields(),
                },
            };
        },
        manual_select_picking_type_fields: function() {
            return [
                {
                    path: "name",
                    renderer: this.picking_type_render_lines_count,
                    display_no_value: true,
                },
            ];
        },
        picking_type_render_lines_count(record, field) {
            return _.template("(${counters}) ${name}")({
                counters: this.$t("misc.lines_count", record),
                name: record.name,
            });
        },
        select_line_table_headers: function() {
            // Convert to v-data-table keys
            let headers = _.map(this.move_line_list_fields(true), function(field) {
                return {
                    text: field.label,
                    value: field.path,
                    // sorting delegated to button
                    sortable: false,
                };
            });
            return headers;
        },
        select_line_table_items: function() {
            const self = this;
            // Convert to v-data-table keys
            let items = _.map(this.state.data.move_lines, function(record) {
                let item_data = {};
                _.forEach(self.move_line_list_fields(true), function(field) {
                    item_data[field.path] = _.result(record, field.path);
                    if (field.renderer) {
                        item_data[field.path] = field.renderer(record, field);
                    }
                });
                item_data["_origin"] = record;
                return item_data;
            });
            return items;
        },
        select_line_move_line_detail_options: function() {
            let options = {
                key_title: "location_src.name",
                group_color: this.utils.colors.color_for("screen_step_todo"),
                card_klass: "loud-labels",
                title_action_field: {action_val_path: "product.barcode"},
                showActions: false,
                list_item_options: {
                    loud_title: true,
                    fields: this.move_line_list_fields(),
                    list_item_klass_maker: function(rec) {
                        return rec.location_will_be_empty
                            ? "location-will-be-empty"
                            : "";
                    },
                },
            };
            return options;
        },
        move_line_list_fields: function(table_mode = false) {
            const self = this;
            let fields = [
                {path: "product.display_name", label: table_mode ? "Product" : null},
                {
                    path: "package_src.name",
                    label: "Pack / Lot",
                    renderer: function(rec, field) {
                        const pkg = _.result(rec, "package_src.name", "");
                        const lot = _.result(rec, "lot.name", "");
                        return lot ? pkg + "\n" + lot : pkg;
                    },
                },
                {
                    path: "quantity",
                    label: "Qty",
                    render_component: "packaging-qty-picker-display",
                    render_options: function(record) {
                        return self.utils.wms.move_line_qty_picker_options(record);
                    },
                },
                {path: "package_src.weight", label: "Weight"},
                {
                    path: "picking.scheduled_date",
                    label: "Date",
                    renderer: function(rec, field) {
                        return self.utils.display.render_field_date(rec, field);
                    },
                },
                {
                    path: "priority",
                    label: table_mode ? "Priority" : null,
                    render_component: "priority-widget",
                    render_options: function(record) {
                        return {priority: parseInt(record.priority || "0", 10)};
                    },
                },
                {
                    path: "location_will_be_empty",
                    render_component: "empty-location-icon",
                    display_no_value: true,
                },
            ];
            if (table_mode) {
                fields.unshift({path: "location_src.name", label: "Location"});
            }
            return fields;
        },
        select_line_move_line_records_grouped(move_lines) {
            return this.utils.wms.group_lines_by_location(move_lines, {});
        },
        toggle_sort_lines_by() {
            this.order_lines_by =
                this.order_lines_by == "priority" ? "location" : "priority";
            return this.list_move_lines(this.current_picking_type().id);
        },
        list_move_lines(picking_type_id) {
            const zone_id = this.current_zone_location().id;
            this.odoo._update_headers(
                this._get_zone_picking_headers(zone_id, picking_type_id)
            );
            return this.wait_call(this.odoo.call("list_move_lines", {}));
        },
        scan_source(barcode) {
            return this.wait_call(
                this.odoo.call("scan_source", {
                    barcode: barcode,
                    confirmation: this.state.data.confirmation_required,
                })
            );
        },
        picking_summary_records_grouped(move_lines) {
            const self = this;
            return this.utils.wms.group_lines_by_location(move_lines, {
                group_key: "location_dest",
                // group_no_title: true,
                prepare_records: _.partialRight(
                    this.utils.wms.group_by_pack,
                    "package_dest"
                ),
                group_color_maker: function(lines) {
                    return "screen_step_todo";
                },
            });
        },
        picking_summary_move_line_list_options: function(move_lines) {
            return {
                group_color: this.state_in(["unload_set_destination"])
                    ? this.utils.colors.color_for("screen_step_done")
                    : this.utils.colors.color_for("screen_step_todo"),
                list_item_options: {
                    actions: [],
                    fields: this.picking_summary_move_line_detail_fields(),
                    list_item_klass_maker: this.utils.wms.move_line_color_klass,
                },
            };
        },
        picking_summary_move_line_detail_fields: function() {
            return [{path: "package_src.name", klass: "loud"}];
        },
    },
    computed: {
        sort_lines_by_btn_label() {
            return this.order_lines_by == "priority"
                ? this.$t("order_lines_by.location")
                : this.$t("order_lines_by.priority");
        },
        device_mode() {
            let _mode = "mobile";
            _.forEach(this.media_queries, function(mode, query) {
                if (window.matchMedia(query).matches) {
                    _mode = mode;
                }
            });
            return _mode;
        },
    },
    data: function() {
        return {
            usage: "zone_picking",
            initial_state_key: "scan_location",
            order_lines_by: "priority",
            scan_destination_qty: 0,
            states: {
                init: {
                    enter: () => {
                        this.wait_call(this.odoo.call("select_zone"));
                    },
                },
                scan_location: {
                    display_info: {
                        title: "Start by scanning a location",
                        scan_placeholder: "Select a zone",
                    },
                    events: {
                        go_back: "on_back",
                    },
                    on_back: () => {
                        this.state_to("init");
                        this.reset_notification();
                    },
                    on_select: selected => {
                        this.wait_call(
                            this.odoo.call("scan_location", {barcode: selected.barcode})
                        );
                    },
                    on_scan: scanned => {
                        this.wait_call(
                            this.odoo.call("scan_location", {barcode: scanned.text})
                        );
                    },
                },
                select_picking_type: {
                    display_info: {
                        title: "Select operation type",
                    },
                    events: {
                        go_back: "on_back",
                    },
                    on_back: () => {
                        this.state_to("init");
                        this.reset_notification();
                    },
                    on_select: selected => {
                        this.list_move_lines(selected.id);
                    },
                },
                select_line: {
                    display_info: {
                        title: "Select move",
                        scan_placeholder: "Scan pack or location",
                    },
                    events: {
                        select: "on_select",
                        go_back: "on_back",
                    },
                    on_back: () => {
                        this.reset_notification();
                        this.wait_call(
                            this.odoo.call("scan_location", {
                                barcode: this.current_zone_location().barcode,
                            })
                        );
                    },
                    on_scan: scanned => {
                        this.scan_source(scanned.text);
                    },
                    on_select: selected => {
                        let path = "package_src.name";
                        let barcode = _.result(selected, path);
                        while (!barcode) {
                            _.forEach(
                                ["lot.name", "product.barcode", "location_src.barcode"],
                                function(path) {
                                    barcode = _.result(selected, path);
                                }
                            );
                        }
                        this.scan_source(barcode);
                    },
                    on_unload_at_destination: () => {
                        this.wait_call(this.odoo.call("prepare_unload", {}));
                    },
                },
                set_line_destination: {
                    display_info: {
                        title: "Set destination",
                        scan_placeholder: "Scan location or package",
                        scan_placeholder_full: "Scan location or package",
                        scan_placeholder_partial: "Scan package",
                    },
                    events: {
                        qty_edit: "on_qty_update",
                    },
                    on_qty_update: qty => {
                        this.scan_destination_qty = parseInt(qty, 10);
                        if (this.state.data.move_line.quantity != qty) {
                            this.state.display_info.scan_placeholder = this.state.display_info.scan_placeholder_partial;
                        } else {
                            this.state.display_info.scan_placeholder = this.state.display_info.scan_placeholder_full;
                        }
                    },
                    on_scan: scanned => {
                        const data = this.state.data;
                        this.wait_call(
                            this.odoo.call("set_destination", {
                                move_line_id: data.move_line.id,
                                barcode: scanned.text,
                                quantity: this.scan_destination_qty,
                                confirmation: data.confirmation_required,
                            })
                        );
                    },
                    on_action: action => {
                        this.state["on_" + action.event_name].call(this);
                    },
                    on_action_stock_out: () => {
                        this.state_set_data(this.state.data, "stock_issue");
                        this.state_to("stock_issue");
                    },
                    on_action_change_pack_lot: () => {
                        this.state_set_data(this.state.data, "change_pack_lot");
                        this.state_to("change_pack_lot");
                    },
                },

                // ---> TODO: pretty equal to cluster picking: shall we move to mixin?
                unload_all: {
                    display_info: {
                        title: "Unload all bins",
                        scan_placeholder: "Scan location",
                    },
                    on_scan: scanned => {
                        this.state_set_data({location_barcode: scanned.text});
                        this.wait_call(
                            this.odoo.call("set_destination_all", {
                                barcode: scanned.text,
                                confirmation: this.state.data.confirmation_required,
                            })
                        );
                    },
                    on_action_split: () => {
                        this.wait_call(this.odoo.call("unload_split", {}));
                    },
                },
                unload_single: {
                    display_info: {
                        title: "Unload single pack",
                        scan_placeholder: "Scan pack",
                    },
                    on_scan: scanned => {
                        this.wait_call(
                            this.odoo.call("unload_scan_pack", {
                                package_id: this.state.data.move_line.package_dest.id,
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
                            this.odoo.call("unload_set_destination", {
                                package_id: this.state.data.move_line.package_dest.id,
                                barcode: scanned.text,
                                confirmation: this.state.data.confirmation_required,
                            })
                        );
                    },
                },
                change_pack_lot: {
                    display_info: {
                        title: "Change pack or lot",
                        scan_placeholder: "Scan pack or lot",
                    },
                    on_scan: scanned => {
                        this.wait_call(
                            this.odoo.call("change_pack_lot", {
                                move_line_id: this.state.data.move_line.id,
                                barcode: scanned.text,
                            })
                        );
                    },
                },
                stock_issue: {
                    enter: () => {
                        this.reset_notification();
                    },
                    on_action: action => {
                        this.state["on_" + action].call(this);
                    },
                    on_confirm_stock_issue: () => {
                        this.wait_call(
                            this.odoo.call("stock_issue", {
                                move_line_id: this.state.data.move_line.id,
                            })
                        );
                    },
                    on_back: () => {
                        this.state_set_data({});
                        this.reset_notification();
                        this.state_to("start_line");
                    },
                },
                zero_check: {
                    on_action: action => {
                        this.state["on_" + action].call(this);
                    },
                    is_zero: zero_flag => {
                        this.wait_call(
                            this.odoo.call("is_zero", {
                                move_line_id: this.state.data.move_line.id,
                                zero: zero_flag,
                            })
                        );
                    },
                    on_action_confirm_zero: () => {
                        this.state.is_zero(true);
                    },
                    on_action_confirm_not_zero: () => {
                        this.state.is_zero(false);
                    },
                },
            },
        };
    },
    // TODO: move this lovely feature to a mixin or provide it to all components.
    props: {
        default_template: {
            type: String,
            default: "mobile",
        },
        media_queries: {
            type: Object,
            default: function() {
                return {
                    "(min-width: 500px)": "desktop",
                };
            },
        },
        compiled_templates: {
            type: Object,
            default: function() {
                return TEMPLATES;
            },
        },
    },
    render(createElement) {
        const tmpl = this.compiled_templates[this.device_mode];
        return tmpl.render.call(this, createElement);
    },
};

process_registry.add("zone_picking", ZonePicking);

export default ZonePicking;
