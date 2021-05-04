/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("choosing-reception-contact", {
    props: ["partners", "fields"],
    template: `
        <div>
            <searchbar
                :input_placeholder="scan_placeholder"
            />
            <contact-list
                v-if="partners && partners.length > 0"
                v-on="$listeners"
                :fields="fields"
                :contacts="partners"
                />
            <div
                v-if="!partners || partners.length === 0"
                >
                There is no reception to process
            </div>
        </div>
    `,
    data: () => ({
        scan_placeholder: "Scan contact / receipt / product",
    }),
});
