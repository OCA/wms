/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ItemDetailMixin} from "/shopfloor_mobile_base/static/wms/src/components/detail/detail_mixin.js";

// TODO: refactor according to new data from backend and maybe merge w/ `detail-lot`
Vue.component("detail-product", {
    mixins: [ItemDetailMixin],
    methods: {
        product_detail_fields() {
            const fields = [{path: "package_dest.name"}, {path: "lot.name"}];
            return this.opts.full_detail
                ? _.concat(fields, this.full_detail_fields())
                : fields;
        },
        full_detail_fields() {
            return [
                // image TODO
                {path: "lot.name", label: "Lot"},
                {path: "expiry_date", label: "Expiry date"},
                {path: "default_code", label: "Internal ref"},
                {path: "barcode", label: "Barcode"},
                {path: "product.supplier_code", label: "Supplier ref"},
            ];
        },
        packaging_detail_fields() {
            return [{path: "name", renderer: this.render_packaging}];
        },
        supplier_detail_fields() {
            return [
                {path: "name", klass: "loud"},
                {path: "product_code", label: "Code"},
                {path: "product_name", label: "Name"},
            ];
        },
        render_packaging(record, field) {
            return [
                record["name"],
                "(" + record["code"] + ")",
                "= " + record["qty"],
            ].join(" ");
        },
    },
    template: `
<div :class="$options._componentTag">
    <item-detail-card
        v-bind="$props"
        :options="{main: true, fields: product_detail_fields(), key_title: 'display_name'}"
        card_color="info lighten-3"
        />

    <div class="suppliers mb-4" v-if="_.result(record, 'suppliers', []).length">
        <separator-title>Suppliers</separator-title>
        <item-detail-card
            v-for="supp in record.suppliers"
            :key="'supp' + supp.id"
            :record="supp"
            :options="{no_title: true, fields: supplier_detail_fields()}"
            />
    </div>

    <div class="packaging mb-4" v-if="opts.full_detail && record.packaging">
        <separator-title>Packaging</separator-title>
        <list
            :records="record.packaging"
            :options="{key_title: 'display_name', list_item_fields: packaging_detail_fields()}"
            />
    </div>
</div>
`,
});
