import {ItemDetailMixin} from "./detail_mixin.js";

Vue.component("detail-location", {
    mixins: [ItemDetailMixin],
    methods: {
        product_list_fields() {
            return [
                {
                    path: "product.display_name",
                    action_val_path: "product.barcode",
                    klass: "loud",
                },
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
    <item-detail-card v-bind="$props" :options="{main: true}">

      <template v-slot:subtitle>
        {{ record.complete_name }}
      </template>

    </item-detail-card>

    <div class="products" v-if="record.reserved_move_lines.length">
        <separator-title>Reserved products</separator-title>

        <list
            :records="record.reserved_move_lines"
            :options="{key_title: 'display_name', list_item_fields: product_list_fields()}"
            />

    </div>

  </div>
`,
});
