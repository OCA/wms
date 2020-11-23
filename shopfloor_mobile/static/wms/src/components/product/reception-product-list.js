/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("reception-product-list", {
    props: {products: {default: []}, fields: undefined},
    template: `
        <div>
            <reception-product
                v-if="products.length > 0"
                v-for="product in products"
                :fields="fields"
                :product="product"
                :key="product.id"
                />
        </div>
    `,
});
