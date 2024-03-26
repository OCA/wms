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
                // Image TODO
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
            return [record.name, "(" + record.code + ")", "= " + record.qty].join(" ");
        },
        locations_by_products_options() {
            return {
                main: false,
                key_title: "name",
                klass: "loud-labels",
            };
        },

        available_product_list_options() {
            return {
                main: true,
                key_title: "display_name",
                klass: "loud-labels",
                title_action_field: {
                    action_val_path: "default_code",
                },
                fields: this.available_product_list_fields(),
            };
        },
        available_product_list_fields() {
            return [{path: "qty_available", label: "Qty on hand"}];
        },
        lot_detail_options() {
            return {
                main: false,
                key_title: "name",
                fields: this.lot_detail_fields(),
                klass: "loud-labels",
            };
        },
        lot_detail_fields() {
            const self = this;
            return [
                {path: "product_name", label: "Product"},
                {path: "quantity", label: "Qty in stock"},
                {
                    path: "expire_date",
                    label: "Expiry date",
                    renderer: function (rec, field) {
                        return self.utils.display.render_field_date(rec, field);
                    },
                },
                {
                    path: "removal_date",
                    label: "Removal date",
                    renderer: function (rec, field) {
                        return self.utils.display.render_field_date(rec, field);
                    },
                },
            ];
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
    <div class="locations" v-if="record.locations.length">
        <separator-title>Locations</separator-title>
        <v-expansion-panels v-if="record.locations.length > 0" flat :color="utils.colors.color_for('detail_main_card')">
            <v-expansion-panel v-for="(location, index) in record.locations" :key="make_component_key(['location', index])">
              <v-expansion-panel-header>
                  <item-detail-card
                      v-bind="$props"
                      :record="location"
                      :key="make_component_key(['location', location.id])"
                      :options="locations_by_products_options()"
                      :card_color="utils.colors.color_for('detail_main_card')"
                      />
              </v-expansion-panel-header>
              <v-expansion-panel-content v-for="(product, i) in location.products">
                <separator-title>Lots</separator-title>
                <item-detail-card
                v-for="(lot, i) in product.lots"
                :record="lot"
                v-bind="$props"
                :key="make_component_key(['lot', lot.id])"
                :options="lot_detail_options()"
                :card_color="utils.colors.color_for('screen_step_todo')"
                />
              </v-expansion-panel-content>

              </v-expansion-panel>
        </v-expansion-panels>
    </div>
</div>
`,
});
