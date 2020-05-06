import {ItemDetailMixin} from "./detail_mixin.js";

Vue.component("detail-location", {
    mixins: [ItemDetailMixin],
    methods: {
        detail_fields() {
            return [
                {path: "lot.name", label: "Lot"},
                {path: "expiry_date", label: "Expiry date"},
                {path: "default_code", label: "Internal ref"},
                {path: "supplier_code", label: "Supplier ref"},
            ];
        },
        product_list_fields() {
            return [
                {path: "lot.name", label: "Lot"},
                {path: "qty_reserved", label: "Reserved"},
                {path: "qty_instock", label: "In stock"},
            ];
        },
        handle_product_click(product) {
            if (this.opts.on_url_change) {
                this.opts.on_url_change(
                    product.pack ? product.pack.barcode : product.barcode
                );
            }
        },
    },
    template: `
  <div :class="$options._componentTag">
    <item-detail-card v-bind="$props" :options="{main: true, fields: detail_fields()}">

      <template v-slot:subtitle>
        {{ record.parent_name }}
      </template>

    </item-detail-card>

    <list class="products mb-2"
      v-if="record.products"
      :records="record.products"
      :options="{key_title: 'display_name', list_item_fields: product_list_fields(), list_item_on_click: handle_product_click}"
      />
  </div>
`,
});
