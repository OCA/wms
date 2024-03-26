/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ItemDetailMixin} from "/shopfloor_mobile_base/static/wms/src/components/detail/detail_mixin.js";

Vue.component("detail-package", {
    mixins: [ItemDetailMixin],
    methods: {
        detail_fields() {
            return [
                {path: "location.name", label: "Location"},
                {path: "weight", label: "Weight (kg)"},
                {path: "packaging.name", label: "Packaging"},
                {path: "storage_type.name", label: "Storage type"},
                {path: "package_type.name", label: "Package type"},
            ];
        },
        product_list_options() {
            return {
                card_klass: "loud-labels",
                key_title: "",
                list_item_options: {
                    fields: this.product_list_fields(),
                    list_item_klass_maker: this.utils.wms.move_line_color_klass,
                },
            };
        },
        product_list_fields() {
            return [
                {
                    path: "product.display_name",
                    action_val_path: "product.barcode",
                    klass: "loud",
                },
                {path: "product.barcode", label: "Barcode"},
                {path: "product.supplier_code", label: "Vendor code"},
                {path: "lot.name", label: "Lot"},
                {path: "quantity", label: "Reserved"},
                {path: "product.qty_available", label: "In stock"},
            ];
        },
    },
    template: `
        <div :class="$options._componentTag">
            <item-detail-card
                v-bind="$props"
                :options="{main: true, fields: detail_fields(), klass: 'loud-labels'}"
                :card_color="utils.colors.color_for('detail_main_card')"
                />

            <div class="products mb-4" v-if="(record.move_lines || []).length">
                <separator-title>Products</separator-title>
                <list
                    :records="record.move_lines"
                    :options="product_list_options()"
                    :key="make_component_key(['product-list'])"
                    />
            </div>

            <div class="pickings" v-if="(record.pickings || []).length">
                <separator-title>Transfers</separator-title>
                <detail-picking
                    v-for="picking in record.pickings"
                    :record="picking"
                    :key="make_component_key(['picking', picking.id])"
                    />
            </div>
        </div>
    `,
});
