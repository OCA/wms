import {ItemDetailMixin} from "./detail_mixin.js";

Vue.component("detail-pack", {
    mixins: [ItemDetailMixin],
    methods: {
        detail_fields() {
            return [
                {path: "location_src.name"},
                {path: "weight"},
                {path: "storage_type"},
                {path: "package_type"},
            ];
        },
        product_list_fields() {
            return [
                {path: "lot.name", label: "Lot"},
                {path: "qty_reserved", label: "Reserved"},
                {path: "qty_instock", label: "In stock"},
            ];
        },
        picking_list_fields() {
            return [
                {path: "ref_and_customer", renderer: this.render_ref_and_customer},
                {path: "qty_reserved", label: "Reserved"},
                {path: "qty_instock", label: "In stock"},
            ];
        },
        render_ref_and_customer(record, field) {
            return "REF-CUST";
        },
    },
    template: `
        <div :class="$options._componentTag">
            <item-detail-card v-bind="$props" :options="{main: true, fields: detail_fields()}" />

            <list class="products mb-2"
                v-if="record.products"
                :records="record.products"
                :options="{key_title: 'display_name', list_item_fields: product_list_fields()}"
                />

            <detail-picking
                v-for="picking in record.pickings"
                :key="picking.id"
                :picking="picking"
                :klass="'listed'"
                />
        </div>
    `,
});
