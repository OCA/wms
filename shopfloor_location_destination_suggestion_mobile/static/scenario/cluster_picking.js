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

// Adds method to compute the title from the record
methods._get_title_from_record = function (record) {
    let cart_title = record?.location_dest?.name || "";
    if (record?.location_destination_suggestions) {
        cart_title = cart_title + " / " + record.location_destination_suggestions;
    }
    return cart_title;
};

// Adds method to set the title property on the record
methods._set_record_title = function (record) {
    const title = this._get_title_from_record(record);
    Vue.set(record, "title", title);
};

// Adds handler to define add the new property on the record
// At component creation
const created_original =
    location_operation_detail_component.extendOptions.created || function () {};

const created_method = function () {
    created_original.bind(this)();
    this._set_record_title(this.record);
};
location_operation_detail_component.extendOptions.created = created_method;

// Adds handler to define add the new property on the record
// At record update
location_operation_detail_component.extendOptions.watch = {
    record: {
        handler(newVal) {
            this._set_record_title(newVal);
        },
        deep: true,
    },
};

// override the title to display the destination location name and suggestion
const location_operation_detail_options_method =
    methods.location_operation_detail_options;
methods.location_operation_detail_options = function () {
    const result = location_operation_detail_options_method.bind(this)();
    result.key_title = "title";
    return result;
};
