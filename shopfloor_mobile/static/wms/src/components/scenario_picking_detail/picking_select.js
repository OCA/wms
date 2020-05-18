/* eslint-disable strict */
/* eslint-disable no-implicit-globals */
import {PickingDetailSelectMixin} from "./mixins.js";

Vue.component("detail-picking-select", {
    mixins: [PickingDetailSelectMixin],
});

Vue.component("picking-select-line-content", {
    props: {
        record: Object,
        options: Object,
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
            <span>{{ record.product.display_name }}</span>
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
    // TODO: `list` no supports passing action components dynamically.
    // Consider moving `edit-action` call to `list_options.list_item_options.actions`.
    template: `
    <div>
        <div :class="record.package_dest ? 'has-pack' : 'no-pack'">
            <span>{{ record.product.display_name }}</span>
            <edit-action class="float-right" :record="record" :options="{click_event:'qty_edit'}" />
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
