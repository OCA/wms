/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("choosing-reception-picking", {
    props: ["pickings", "fields"],
    template: `
        <div>
            <searchbar
                :input_placeholder="scan_placeholder"
            />
            <item-detail-card
                v-for="picking in pickings"
                :record="picking"
                :options="{fields: fields, full_detail: true, on_click_action: () => $emit('select-picking', picking.id)}"
                />
            <div
                v-if="!pickings || pickings.length === 0"
                >
                There is no pickings
            </div>
        </div>
    `,
    data: () => ({
        scan_placeholder: "Scan a picking id",
    }),
});
