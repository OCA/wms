/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ItemDetailMixin} from "/shopfloor_mobile_base/static/wms/src/components/detail/detail_mixin.js";

Vue.component("detail-simple-product", {
    props: ["product", "fields", "selected"],
    mixins: [ItemDetailMixin],
    methods: {
        line_color: function(line) {
            if (line.done) {
                return this.utils.colors.color_for("pack_line_done");
            }
            if (line.qtyDone === line.qty) {
                return this.utils.colors.color_for("quantity_done");
            }
            return undefined;
        },
    },
    template: `
    <item-detail-card
        :record="product"
        :options="{fields: fields}"
        :card_color="line_color(product)"
        :outlined="selected"
    >
        <template v-slot:after_details>
            <v-container>
                <slot name="actions">
                </slot>
            </v-container>
        </template>
    </item-detail-card>
    `,
});
