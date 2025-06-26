/**
 * Copyright 2025 ACSONE SA/NV (https://acsone.eu)
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
 */

const location_operation_detail_component = Vue.component(
    "detail-location-destination-operation"
);
const methods = location_operation_detail_component.extendOptions.methods;
const location_operation_detail_fields_method =
    methods.location_operation_detail_fields;

// Adds the destination locations suggestions to the destination location component
methods.location_operation_detail_fields = function () {
    const result = location_operation_detail_fields_method.bind(this)();
    const new_result = [
        ...result,
        {path: "location_destination_suggestions", label: "Destination Suggestions"},
    ];
    return new_result;
};
