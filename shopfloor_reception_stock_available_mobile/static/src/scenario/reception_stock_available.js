/**
 * Copyright 2026 ACSONE SA/NV
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

const reception_scenario = process_registry.get("reception");
const baseMethods = reception_scenario.component.methods || {};

const ReceptionStockAvailable = process_registry.extend("reception", {
    methods: {
        ...baseMethods,

        /**
         * Extend product detail options to display immediately usable quantity
         * when the product stock is negative (indicating urgent demand).
         */
        line_product_detail_options: function () {
            const options = baseMethods.line_product_detail_options.bind(this)();

            const usableQty = _.result(
                this.line_being_handled,
                "product.immediately_usable_qty"
            );

            if (usableQty !== undefined && usableQty < 0) {
                options.fields.push({
                    path: "product.immediately_usable_qty",
                    label: this.$t("reception.urgent_qties"),
                    klass: "loud red",
                    renderer: (rec, field) => {
                        const qty = _.result(rec, field.path);
                        const uomName = _.result(rec, "product.uom.name");
                        return `${-qty} ${uomName}`;
                    },
                });
            }

            return options;
        },
    },
});

process_registry.replace("reception", ReceptionStockAvailable);

export default ReceptionStockAvailable;
