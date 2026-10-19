/**
 * Copyright 2026 ACSONE SA/NV
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

const reception_scenario = process_registry.get("reception");
const baseMethods = reception_scenario.component.methods || {};

const ReceptionProductPackageType = process_registry.extend("reception", {
    methods: {
        ...baseMethods,

        line_product_detail_options: function () {
            const options = baseMethods.line_product_detail_options.bind(this)();

            options.fields.push({
                path: "product.package_type.display_name",
                label: this.$t("common.package_type"),
            });

            return options;
        },
    },
});

process_registry.replace("reception", ReceptionProductPackageType);

export default ReceptionProductPackageType;
