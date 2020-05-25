/* eslint-disable strict */
/* eslint-disable no-implicit-globals */
import {PickingDetailSelectMixin} from "./mixins.js";
import {ItemDetailMixin} from "../detail/detail_mixin.js";

Vue.component("detail-picking-select", {
    mixins: [PickingDetailSelectMixin],
    methods: {
        _get_available_list_item_actions() {
            // TODO: we should probably make the 1st class citizens w/ their own object class.
            return {
                action_qty_edit: {
                    comp_name: "edit-action",
                    get_record: function(rec, action) {
                        return rec;
                    },
                    options: {
                        click_event: "qty_edit",
                    },
                    enabled: function(rec, action) {
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
    template: `
    <div>
        <div class="has_pack" v-if="record.package_dest">
            <div class="item-counter">
                <span>{{ index + 1 }} / {{ count }}</span>
            </div>
            <span>{{ record.package_dest.name }}</span>
        </div>
        <div class="no_pack" v-if="!record.package_dest">
            <div class="item-counter">
                <span>{{ index + 1 }} / {{ count }}</span>
            </div>
            <span class="clickable" @click="on_detail_action(record.product, {action_val_path: 'barcode'})">
                {{ record.product.display_name }}
                <btn-info-icon />
            </span>
            <div class="lot" v-if="record.lot">
                <span class="label">Lot:</span> <span>{{ record.lot.name }}</span>
            </div>
            <div class="qty">
                <span class="label">Qty:</span> <span>{{ record.quantity }}</span>
            </div>
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
            <div class="qty">
                <span class="label">Qty:</span> <span>{{ record.qty_done }} / {{ record.quantity }}</span>
            </div>
        </div>
    </div>
  `,
});
