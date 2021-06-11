/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ItemDetailMixin} from "/shopfloor_mobile_base/static/wms/src/components/detail/detail_mixin.js";

Vue.component("detail-transfer", {
    mixins: [ItemDetailMixin],
    methods: {
        detail_fields() {
            const self = this;
            return [
                {
                    path: "scheduled_date",
                    label: "Scheduled on",
                    renderer: function(rec, field) {
                        return self.utils.display.render_field_date(rec, field);
                    },
                },
                {
                    path: "operation_type.name",
                    label: "Operation type",
                },
                {path: "carrier.name", label: "Carrier"},
                {path: "priority", label: "Priority"},
                {path: "note"},
            ];
        },
        picking_detail_options() {
            return _.defaults({}, this.opts, {
                main: true,
                klass: "loud-labels",
                title_action_field: null,
            });
        },
        line_list_options() {
            return {
                card_klass: "loud-labels",
                key_title: "",
                list_item_options: {
                    fields: this.line_list_fields(),
                    list_item_klass_maker: this.utils.wms.move_line_color_klass,
                },
            };
        },
        line_list_fields() {
            const self = this;
            return [
                {
                    path: "product.display_name",
                    action_val_path: "product.barcode",
                    klass: "loud",
                },
                {
                    path: "package_src.name",
                    label: "Pack",
                    action_val_path: "package_src.name",
                },
                {path: "lot.name", label: "Lot", action_val_path: "lot.name"},
                {
                    path: "product.qty_reserved",
                    label: "Qty reserved",
                    render_component: "packaging-qty-picker-display",
                    render_options: function(record) {
                        return self.utils.wms.move_line_qty_picker_options(record);
                    },
                },
                {
                    path: "product.qty_available",
                    label: "Qty in stock",
                    render_component: "packaging-qty-picker-display",
                    render_options: function(record) {
                        return self.utils.wms.move_line_qty_picker_options(record);
                    },
                },
            ];
        },
        grouped_lines() {
            return this.utils.wms.group_lines_by_locations(this.record.move_lines);
        },
    },
    template: `
    <div :class="$options._componentTag">

        <detail-picking
            :key="record.id"
            :record="record"
            :options="picking_detail_options()"
            :card_color="utils.colors.color_for('detail_main_card')"
            >
            <!-- TODO: this actions should come from a registry -->
            <template v-slot:actions>
                <speed-dial :fab_btn_attrs="{small: true}" :options="{fab_btn_icon: 'mdi-pencil'}" v-if="record.carrier">
                    <v-btn
                        fab
                        dark
                        small
                        color="green"
                        title="Edit carrier"
                        @click="$router.push({'name': 'edit_form', params: {form_name: 'form_edit_stock_picking', record_id: record.id}})"
                    >
                        <v-icon>mdi-truck-outline</v-icon>
                    </v-btn>
                </speed-dial>
            </template>
        </detail-picking>

        <div class="lines" v-if="(record.move_lines || []).length">
            <div v-for="group in grouped_lines()">
                <separator-title>
                    {{group.location_src.name}} -> {{ group.location_dest.name }}
                </separator-title>
                <list
                    :records="group.records"
                    :key="'group-' + group.key"
                    :options="line_list_options()"
                    />
            </div>
        </div>
    </div>
`,
});
