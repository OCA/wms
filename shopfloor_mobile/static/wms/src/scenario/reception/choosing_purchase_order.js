/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("choosing-purchase-order", {
    props: ["orders", "fields"],
    template: `
        <div>
            <searchbar
                :input_placeholder="scan_placeholder"
            />
            <item-detail-card
                v-for="order in orders"
                :record="order"
                :options="{fields: fields, full_detail: true, on_click_action: () => $emit('select-order', order.id)}"
                />
            <div
                v-if="!orders || orders.length === 0"
                >
                There is no purchase orders
            </div>
        </div>
    `,
    data: () => ({
        scan_placeholder: "Scan a purchase order",
    }),
});
