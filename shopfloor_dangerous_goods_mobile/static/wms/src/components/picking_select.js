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
    let has_lq = record.has_lq_products;
    // At this point this line could have been grouped by pack
    // and we might have sibling lines
    if (!has_lq && record._grouped_by_pack) {
        has_lq = _.find(record._pack_lines || [], ["has_lq_products", true]);
    }
    return has_lq ? "has-lq-products" : "";
};
