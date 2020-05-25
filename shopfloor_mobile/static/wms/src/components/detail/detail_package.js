import {ItemDetailMixin} from "./detail_mixin.js";

Vue.component("detail-package", {
    mixins: [ItemDetailMixin],
    methods: {
        detail_fields() {
            return [
                {path: "location_src.name"},
                {path: "weight"},
                {path: "storage_type.name"},
                {path: "package_type.name"},
            ];
        },
        product_list_fields() {
            return [
                {path: "lot.name", label: "Lot"},
                {path: "product.qty_reserved", label: "Reserved"},
                {path: "product.qty_available", label: "In stock"},
            ];
        },
    },
    template: `
        <div :class="$options._componentTag">
            <item-detail-card v-bind="$props" :options="{main: true, fields: detail_fields()}" />


            <div class="products mb-4" v-if="(record.move_lines || []).length">
                <separator-title>Products</separator-title>
                <item-detail-card
                    v-for="line in record.move_lines"
                    :record="line"
                    :key="'line-' + line.id"
                    :options="{key_title: 'product.display_name', fields: product_list_fields()}"
                    />
            </div>

            <div class="pickings" v-if="(record.pickings || []).length">
                <separator-title>Transfers</separator-title>
                <detail-picking
                    v-for="picking in record.pickings"
                    :key="picking.id"
                    :record="record"
                    />
            </div>
        </div>
    `,
});

// <list class="products mb-2"
//                 v-if="record.move_lines"
//                 :records="record.move_lines"
//                 :options="{key_title: 'display_name', list_item_fields: product_list_fields()}"
//                 />
