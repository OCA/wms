import {ItemDetailMixin} from "./detail_mixin.js";

// TODO: this should probably trashed in favour of detail-transfer
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
        :picking="record.picking"
        :options="{main: true}"
        />
    <item-detail-card v-bind="$props" :options="op_card_options()" />
  </div>
`,
});
