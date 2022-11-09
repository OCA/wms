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
        no_pack_list_item_options(record) {
            const opts = this.utils.wms.move_line_product_detail_options(record);
            opts.fields.unshift({
                path: "product.display_name",
                action_val_path: "product.barcode",
            });
            return opts;
        },
    },
    template: `
    <div>
        <div class="has_pack" v-if="record.package_dest">
            <span class="clickable" @click="on_detail_action(record.package_dest, {action_val_path: 'name'})">
                <btn-info-icon />
                {{ record.package_dest.name }}
            </span>
        </div>
        <div class="no_pack" v-if="!record.package_dest">
            <list-item v-bind="$props" :options="no_pack_list_item_options(record)" />
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
    template: `
    <div>
        <div :class="record.package_dest ? 'has-pack' : 'no-pack'">
            <span>{{ record.product.display_name }}</span>
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
