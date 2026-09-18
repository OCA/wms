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
                {path: "location.name", label: this.$t("common.location")},
                {path: "weight", label: this.$t("common.weight_kg")},
                {path: "packaging.name", label: this.$t("product.packaging")},
                {
                    path: "storage_type.name",
                    label: this.$t("common.package_type"),
                },
                {
                    path: "package_type.name",
                    label: this.$t("common.package_type"),
                },
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
                {path: "product.barcode", label: this.$t("common.barcode")},
                {
                    path: "product.supplier_code",
                    label: this.$t("common.vendor_code"),
                },
                {path: "lot.name", label: this.$t("common.lot")},
                {path: "quantity", label: this.$t("common.reserved")},
                {
                    path: "product.qty_available",
                    label: this.$t("common.in_stock"),
                },
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
                <separator-title>{{ $t("common.products") }}</separator-title>
                <list
                    :records="record.move_lines"
                    :options="product_list_options()"
                    :key="make_component_key(['product-list'])"
                    />
            </div>

            <div class="pickings" v-if="(record.pickings || []).length">
                <separator-title>{{ $t("common.transfers") }}</separator-title>
                <detail-picking
                    v-for="picking in record.pickings"
                    :record="picking"
                    :key="make_component_key(['picking', picking.id])"
                    />
            </div>
        </div>
    `,
});
