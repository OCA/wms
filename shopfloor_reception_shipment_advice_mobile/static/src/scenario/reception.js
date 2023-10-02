/**
 * Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
 **/

import {ScenarioBaseMixin} from "/shopfloor_mobile_base/static/wms/src/scenario/mixins.js";
import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";
import {reception_states} from "/shopfloor_reception_mobile/static/src/scenario/reception_states.js";

const reception_scenario = process_registry.get("reception");

const select_move_from_record =
    reception_scenario.component.methods.select_move_from_record;
const select_move_from_record_options =
    reception_scenario.component.methods.select_move_from_record_options;
const select_move_from_record_key =
    reception_scenario.component.methods.select_move_from_record_key;
const current_doc = reception_scenario.component.methods.current_doc;
const computed_moves_to_select = reception_scenario.component.computed.moves_to_select;

// Get the original template
const template = reception_scenario.component.template;
// And inject the new state template (for this module) into it
const pos = template.indexOf("</Screen>");
const new_template =
    template.substring(0, pos) +
    `

<template v-if="state_is('manual_selection_shipment')">

<manual-select
    class="with-progress-bar"
    :records="dock_available_shipments()"
    :options="manual_select_shipment_options()"
    :key="make_state_component_key(['reception', 'manual-select-shipment'])"
    />
<div class="button-list button-vertical-list full">
    <v-row align="center">
        <v-col class="text-center" cols="12">
            <btn-back />
        </v-col>
    </v-row>
</div>

</template>

` +
    template.substring(pos);

const ReceptionShipmentAdvice = process_registry.extend("reception", {
    template: new_template,

    "methods._get_odoo_params": function () {
        const params = this.$super(ScenarioBaseMixin)._get_odoo_params();
        const shipment = this._get_current_shipment();
        if (_.isUndefined(params.headers)) {
            params.headers = {};
        }
        if (!_.isEmpty(shipment)) {
            _.defaults(params.headers, this._get_reception_headers(shipment.id));
        }
        return params;
    },
    "methods._get_reception_headers": function (shipment_id) {
        const res = {};
        if (_.isInteger(shipment_id)) {
            res["SERVICE-CTX-SHIPMENT-ID"] = shipment_id;
        }
        return res;
    },
    "methods._get_current_shipment": function () {
        if (["select_document", "manual_selection"].includes(this.current_state_key)) {
            return {};
        }
        const data = this.state_get_data("select_move");
        if (_.isEmpty(data) || _.isEmpty(data.shipment)) {
            return {};
        }
        return data.shipment;
    },

    /* Added function for the new state : manual_selection_shipment */
    "methods.dock_available_shipments": function () {
        return this.state.data.shipments;
    },
    "methods.manual_select_shipment_options": function () {
        return {
            group_title_default: "Available shipments",
            group_color: this.utils.colors.color_for("screen_step_todo"),
            showActions: false,
            list_item_options: {
                key_title: "name",
                loud_title: true,
                title_action_field: {
                    action_val_path: "name",
                },
                fields: this.select_document_display_fields(),
            },
        };
    },
    "methods._get_states": function () {
        let states = reception_states.bind(this)();
        const placeholder = states.select_document.display_info.scan_placeholder();
        const get_odoo_call_data = states.select_move.get_odoo_call_data;
        states["manual_selection_shipment"] = {
            title: "Choose a shipment",
            events: {
                select: "on_select",
                go_back: "on_back",
            },
            on_select: (selected) => {
                this.wait_call(
                    this.odoo.call("scan_document", {
                        barcode: selected.name,
                    })
                );
            },
            on_back: () => {
                this.state_to("select_document");
                this.reset_notification();
                this.reset_picking_filter();
            },
        };
        states.select_document.display_info.scan_placeholder = () => {
            return placeholder + " / dock";
        };
        /* Extension of existing states function */
        states.select_move.get_odoo_call_data = () => {
            const data = get_odoo_call_data();
            const shipment = this.state.data.shipment;
            if (shipment) {
                data.shipment_id = shipment.id;
            }
            return data;
        };
        return states;
    },
    /* Extension of existing functions */
    "computed.moves_to_select": function () {
        const shipment = this.state.data.shipment;
        if (shipment) {
            return _.result(this.state, "data.shipment.planned_moves", []);
        }
        return computed_moves_to_select.bind(this)();
    },
    "methods.current_doc": function () {
        const data = this.state_get_data("select_move");
        if (_.isEmpty(data.shipment)) {
            return current_doc.bind(this)();
        }
        return {
            record: data.shipment,
            identifier: data.shipment.name,
        };
    },
    "methods.select_move_from_record": function () {
        const shipment = this.state.data.shipment;
        if (shipment) {
            return shipment;
        }
        return select_move_from_record.bind(this)();
    },
    "methods.select_move_from_record_options": function () {
        const shipment = this.state.data.shipment;
        const options = select_move_from_record_options.bind(this)();
        if (shipment) {
            options.fields = [{path: "dock.name", label: "Dock"}];
        }
        return options;
    },
    "methods.select_move_from_record_key": function () {
        const shipment = this.state.data.shipment;
        if (shipment) {
            return this.make_state_component_key([
                "reception-select-move-from-recordl",
                shipment.id,
            ]);
        }
        return select_move_from_record_key.bind(this)();
    },
});

process_registry.replace("reception", ReceptionShipmentAdvice);
