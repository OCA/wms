/* eslint-disable strict */
/* eslint-disable no-implicit-globals */
import {PickingDetailMixin} from "../detail/detail_picking.js";

Vue.component("checkout-picking-change-qty", {
    mixins: [PickingDetailMixin],
    template: `
<div class="checkout-picking-change-qty" v-if="!_.isEmpty(picking)">

    <detail-picking :picking="picking" />

    TODO
</div>
`,
});
