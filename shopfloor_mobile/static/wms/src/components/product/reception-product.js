/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("reception-product", {
    props: ["product", "fields"],
    methods: {
        line_color: function(line) {
            if (line.done) {
                return this.utils.colors.color_for("pack_line_done");
            }
        },
    },
    template: `
    <item-detail-card
        :record="product"
        :options="{fields: fields}"
        :card_color="line_color(product)"
        >
    </item-detail-card>
    `,
});
