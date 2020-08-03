import {ItemDetailMixin} from "./detail_mixin.js";

Vue.component("detail-lot", {
    mixins: [ItemDetailMixin],
    methods: {
        lot_detail_fields() {
            return [
                {
                    path: "expire_date",
                    label: "Expiry date",
                    renderer: this.utils.misc.render_field_date,
                },
                {
                    path: "removal_date",
                    label: "Removal date",
                    renderer: this.utils.misc.render_field_date,
                },
            ];
        },
        supplier_detail_fields() {
            return [
                {path: "name", klass: "loud"},
                {path: "product_code", label: "Code"},
                {path: "product_name", label: "Name"},
            ];
        },
        render_packaging(record, field) {
            return [record["name"], record["qty"] + " " + record["qty_unit"]].join(
                " - "
            );
        },
    },
    template: `
    <div :class="$options._componentTag">
        <item-detail-card :key="'prod-' + record.product.id" v-bind="$props" :options="{main: true, key_title: 'product.display_name'}" />

        <!-- TODO: handle image here -->

        <item-detail-card :key="'lot-' + record.id" v-bind="$props" :options="{key_title: 'name', fields: lot_detail_fields()}" />

        <div class="suppliers mb-4" v-if="record.product.suppliers.length">
            <separator-title>Suppliers</separator-title>
            <item-detail-card
                v-for="supp in record.product.suppliers"
                :key="'supp' + supp.id"
                :record="supp"
                :options="{no_title: true, fields: supplier_detail_fields()}" />
        </div>
        // TODO packaging
        <list class="packaging pb-2"
            v-if="opts.full_detail && record.packaging"
            :records="record.packaging"
            :options="{key_title: 'display_name', list_item_fields: packaging_detail_fields()}"
            />
    </div>
`,
});
