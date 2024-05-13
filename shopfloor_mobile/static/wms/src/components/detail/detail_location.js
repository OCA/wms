/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ItemDetailMixin} from "/shopfloor_mobile_base/static/wms/src/components/detail/detail_mixin.js";

Vue.component("detail-location", {
    mixins: [ItemDetailMixin],
    methods: {
        product_list_options() {
            return {
                key_title: "display_name",
                card_klass: "loud-labels",
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
                {path: "product.supplier_code", label: "Vendor code", klass: "loud"},
                {
                    path: "package_src.name",
                    label: "Pack",
                    action_val_path: "package_src.name",
                },
                {path: "lot.name", label: "Lot", action_val_path: "lot.name"},
                {path: "product.qty_reserved", label: "Qty reserved"},
                {path: "product.qty_available", label: "Qty in stock"},
            ];
        },
    },
    template: `
  <div :class="$options._componentTag">
    <item-detail-card
      v-bind="$props"
      :options="{main: true}"
      :card_color="utils.colors.color_for('detail_main_card')">

      <template v-slot:subtitle>
        {{ record.complete_name }}
      </template>

    </item-detail-card>

    <div class="products" v-if="record.reserved_move_lines.length">
        <separator-title>Reserved products</separator-title>

        <list
            :records="record.reserved_move_lines"
            :options="product_list_options()"
            />

    </div>

  </div>
`,
});
