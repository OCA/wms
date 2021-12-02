/**
 * Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component(
    "picking-select-package-content"
).extendOptions.methods.get_wrapper_klass = function (record) {
    return record.has_lq_products ? "has-lq-products" : "";
};

Vue.component(
    "picking-select-line-content"
).extendOptions.methods.get_wrapper_klass = function (record) {
    return record.has_lq_products ? "has-lq-products" : "";
};
