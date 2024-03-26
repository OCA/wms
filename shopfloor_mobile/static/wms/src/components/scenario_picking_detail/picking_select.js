/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */
/* eslint-disable strict */
/* eslint-disable no-implicit-globals */
import {PickingDetailSelectMixin} from "./mixins.js";
import {ItemDetailMixin} from "/shopfloor_mobile_base/static/wms/src/components/detail/detail_mixin.js";

Vue.component("detail-picking-select", {
    mixins: [PickingDetailSelectMixin],
    methods: {
        _get_available_list_item_actions() {
            // TODO: we should probably make the 1st class citizens w/ their own object class.
            return {
                action_qty_edit: {
                    comp_name: "edit-action",
                    get_record: function (rec, action) {
                        return rec;
                    },
                    get_options: function (rec, action) {
                        return {click_event: "qty_edit"};
                    },
                    enabled: function (rec, action) {
                        return true;
                    },
                },
            };
        },
    },
});

Vue.component("picking-select-line-content", {
    mixins: [ItemDetailMixin],
    props: {
        index: Number,
        count: Number,
    },
    methods: {
        with_pack_list_item_options(record) {
            let fields = [];
            // Display detail fields on demand if the package contains only 1 line
            if (
                this.options.show_oneline_package_content &&
                record.package_dest.move_line_count == 1
            ) {
                fields = [
                    {path: "product.display_name", label: "Product"},
                    {path: "lot.name", label: "Lot"},
                ];
            }
            return {
                main: true,
                show_title: true,
                loud_title: true,
                key_title: "package_dest.name",
                title_action_field: {action_val_path: "package_dest.name"},
                fields: fields,
            };
        },
        without_pack_list_item_options(record) {
            const opts = this.utils.wms.move_line_product_detail_options(record);
            const action_val_path = record.product.barcode
                ? "product.barcode"
                : "product.default_code";
            opts.title_action_field = {action_val_path: action_val_path};
            opts.show_title = true;
            opts.loud_title = true;
            return opts;
        },
        get_wrapper_klass(record) {
            return "";
        },
    },
    computed: {
        pack_list_item_options() {
            if (this.record.package_dest) {
                return this.with_pack_list_item_options(this.record);
            }
            return this.without_pack_list_item_options(this.record);
        },
    },
    template: `
    <div>
        <div :class="[record.package_dest ? 'has-pack' : 'no-pack', get_wrapper_klass(record)]">
            <list-item v-bind="$props" :options="pack_list_item_options" />
        </div>
    </div>
  `,
});

Vue.component("picking-select-package-content", {
    props: {
        record: Object,
        options: Object,
        index: Number,
        count: Number,
    },
    methods: {
        get_wrapper_klass(record) {
            return "";
        },
    },
    // TODO: We should update the layout of this component so that it's in line
    // with the refactor done to "picking-select-line-content":
    // https://github.com/OCA/wms/pull/583
    template: `
    <div>
        <div :class="[record.package_dest ? 'has-pack' : 'no-pack', get_wrapper_klass(record)]">
            <span class="record-name">{{ record.product.display_name }}</span>
            <div class="lot" v-if="record.lot">
                <span class="label">Lot:</span> <span>{{ record.lot.name }}</span>
            </div>
            <div class="qty done">
                <span class="label">Taken:</span>
                <packaging-qty-picker-display
                    :key="make_component_key(['qty-picker-widget', 'taken', record.id])"
                    v-bind="utils.wms.move_line_qty_picker_props(record, {qtyInit: record.qty_done})"
                    />
            </div>
            <div class="qty requested">
                <span class="label">Requested:</span>
                <packaging-qty-picker-display
                    :key="make_component_key(['qty-picker-widget', 'requested', record.id])"
                    v-bind="utils.wms.move_line_qty_picker_props(record, {qtyInit: record.quantity})"
                    />
            </div>
            <div class="vendor-code">
                <span class="label">Vendor code:</span> <span>{{ record.product.supplier_code }}</span>
            </div>
        </div>
    </div>
  `,
});
