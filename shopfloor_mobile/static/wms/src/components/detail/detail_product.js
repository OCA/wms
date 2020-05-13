import {ItemDetailMixin} from "./detail_mixin.js";

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
                {path: "supplier_code", label: "Supplier ref"},
            ];
        },
        packaging_detail_fields() {
            return [{path: "name", renderer: this.render_packaging}];
        },
        render_packaging(record, field) {
            return [record["name"], record["qty"] + " " + record["qty_unit"]].join(
                " - "
            );
        },
    },
    template: `
  <div :class="$options._componentTag">
      <item-detail-card v-bind="$props" :options="{main: true, fields: product_detail_fields(), key_title: 'display_name'}" />

      <list class="packagings pb-2"
          v-if="opts.full_detail && record.packagings"
          :records="record.packagings"
          :options="{key_title: 'display_name', list_item_fields: packaging_detail_fields()}"
          />
  </div>
`,
});
