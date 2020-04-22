/* eslint-disable strict */
/* eslint-disable no-implicit-globals */
import {CheckoutPickingDetailMixin} from "./mixins.js";

Vue.component("checkout-picking-change-qty", {
    mixins: [CheckoutPickingDetailMixin],
    template: `
<div class="checkout-picking-change-qty" v-if="!_.isEmpty(picking)">

    <checkout-picking-detail :picking="picking" />

    TODO
</div>
`,
});
