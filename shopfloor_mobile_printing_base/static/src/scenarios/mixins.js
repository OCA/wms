/**
 * Copyright 2025 ACSONE SA/NV
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
 */

import {ScenarioBaseMixin} from "/shopfloor_mobile_base/static/wms/src/scenario/mixins.js";

const methods = ScenarioBaseMixin.methods;
const data_method = ScenarioBaseMixin.data;

const on_call_success_method = methods.on_call_success;

methods.on_call_success = function (result) {
    // This will fill in the 'allow_print_label' value from service call result
    on_call_success_method.bind(this)(result);
    if (result.allow_print_label) {
        this.set_allow_print_label(result.allow_print_label);
    }
};

methods.set_allow_print_label = function (allow_print_label) {
    this.allow_print_label = allow_print_label;
};

methods._print_label_allowed = function () {
    // Use this method in scenarios to display the component or not
    // TODO: Should this be part of the python code in service response
    // depending on the state ?
    return this.allow_print_label;
};

ScenarioBaseMixin.data = function () {
    const result = data_method();
    const new_result = {
        ...result,
        allow_print_label: false,
    };
    return new_result;
};
