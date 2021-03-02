/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ItemDetailMixin} from "/shopfloor_mobile_base/static/wms/src/components/detail/detail_mixin.js";

// TODO: this should be probably merged or combined w/ detail-product
Vue.component("detail-lot", {
    mixins: [ItemDetailMixin],
    methods: {
        lot_detail_options() {
            return {
                main: true,
                key_title: "name",
                fields: this.lot_detail_fields(),
                klass: "loud-labels",
            };
        },
        lot_detail_fields() {
            const self = this;
            return [
                {
                    path: "expire_date",
                    label: "Expiry date",
                    renderer: function(rec, field) {
                        return self.utils.display.render_field_date(rec, field);
                    },
                },
                {
                    path: "removal_date",
                    label: "Removal date",
                    renderer: function(rec, field) {
                        return self.utils.display.render_field_date(rec, field);
                    },
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
            return [
                record["name"],
                "(" + record["code"] + ")",
                "= " + record["qty"],
            ].join(" ");
        },
        packaging_detail_fields() {
            return [{path: "name", renderer: this.render_packaging}];
        },
    },
    template: `
    <div :class="$options._componentTag">
        <item-detail-card
            v-bind="$props"
            :key="make_component_key(['product'])"
            :options="{main: true, key_title: 'product.display_name'}"
            :card_color="utils.colors.color_for('detail_main_card')"
            />

        <!-- TODO: handle image here -->

        <item-detail-card
            v-bind="$props"
            :key="make_component_key(['lot'])"
            :options="lot_detail_options()"
            :card_color="utils.colors.color_for('detail_main_card')"
            />


        <div class="suppliers mb-4" v-if="record.product.suppliers.length">
            <separator-title>Suppliers</separator-title>
            <item-detail-card
                v-for="supp in record.product.suppliers"
                :key="'supp' + supp.id"
                :record="supp"
                :options="{no_title: true, fields: supplier_detail_fields()}" />
        </div>

        <div class="packaging pb-2" v-if="opts.full_detail && record.product.packaging">
            <separator-title>Packaging</separator-title>
            <list
                :records="record.product.packaging"
                :options="{key_title: 'display_name', list_item_fields: packaging_detail_fields()}"
                />
        </div>
    </div>
`,
});
