/* eslint-disable strict */
/* eslint-disable no-implicit-globals */
import {CheckoutPickingDetailSelectMixin} from "./mixins.js";


Vue.component("checkout-picking-detail-select", {
    mixins: [CheckoutPickingDetailSelectMixin],
});

Vue.component("checkout-select-line-content", {
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
                <span class="label">Qty:</span> <span>{{ record.product.qty }}</span>
            </div>
        </div>
    </div>
  `,
});

Vue.component("checkout-select-package-content", {
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
