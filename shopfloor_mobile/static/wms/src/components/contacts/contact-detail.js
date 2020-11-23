/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("contact-detail", {
    props: ["contact", "fields"],
    template: `
        <item-detail-card
            :record="contact"
            :options="{fields: fields, full_detail: true, on_click_action: () => $emit('select-contact', contact.id)}"
            />
    `,
});
