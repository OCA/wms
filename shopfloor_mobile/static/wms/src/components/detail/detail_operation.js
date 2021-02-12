/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ItemDetailMixin} from "/shopfloor_mobile_base/static/wms/src/components/detail/detail_mixin.js";

// TODO: this should probably trashed in favour of detail-transfer
// ATM is used only by single pack transfer to display package level info.
Vue.component("detail-operation", {
    mixins: [ItemDetailMixin],
    methods: {
        detail_fields() {
            return [
                {
                    path: "location_src.name",
                    label: "Source",
                    action_val_path: "location_src.barcode",
                },
                {
                    path: "location_dest.name",
                    label: "Destination",
                    action_val_path: "location_dest.barcode",
                },
                {path: "product.display_name", action_val_path: "product.barcode"},
                {path: "product.supplier_code", label: "Vendor code", klass: "loud"},
                {path: "package_dest.name", action_val_path: "package_dest.barcode"},
                {path: "lot.name", action_val_path: "lot.barcode"},
            ];
        },
        op_card_options() {
            return {
                loud: true,
                no_title: true,
                fields: this.detail_fields(),
            };
        },
    },
    template: `
  <div :class="$options._componentTag">
    <detail-picking
        :key="record.picking.id"
        :record="record.picking"
        :options="{main: true}"
        />
    <item-detail-card v-bind="$props" :options="op_card_options()" />
  </div>
`,
});
