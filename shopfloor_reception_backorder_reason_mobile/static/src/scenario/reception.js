/**
 * Copyright 2025 ACSONE SA/NV (https://acsone.eu)
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
 */

import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

const ReceptionScenario = process_registry.get("reception");
// const _get_states = ReceptionScenario.component.methods._get_states;
const data_result_method = ReceptionScenario.component.data;

// Get the original template of the reception scenario
let template = ReceptionScenario.component.template;
ReceptionScenario.component.template = template.replace(
    "</Screen>",
    `
 <div v-if="state_is('choose_backorder_reason')">
    <manual-select
            :records="state.data.backorder_reasons"
            :key="make_state_component_key(['reception', 'select-backorder-reason'])"
            :options="manual_select_options_for_choose_backorder_reason()"
            v-on:select="state.on_select"
            />
        <div class="button-list button-vertical-list full">
            <v-row align="center">
                <v-col class="text-center" cols="12">
                    <btn-back />
                </v-col>
            </v-row>
        </div>
</div>
</Screen>
`
);

ReceptionScenario.component.methods.backorder_reason_fields = function () {
    return [
        {
            path: "backorder_action_to_do.label",
            label: "Action",
        },
    ];
};

ReceptionScenario.component.methods.manual_select_options_for_choose_backorder_reason =
    function () {
        return {
            list_item_options: {
                key_title: "name",
                loud_title: true,
                fields: this.backorder_reason_fields(),
            },
        };
    };

let data = function () {
    // we must bin the original method to this to put it into
    // the object context
    let result = data_result_method.bind(this)();

    result.states.choose_backorder_reason = {
        display_info: {
            title: "Choose Backorder Reason",
        },
        events: {
            go_back: "on_back",
        },
        on_select: (selected) => {
            this.wait_call(
                this.odoo.call("choose_backorder_reason", {
                    picking_id: this.state.data.picking.id,
                    reason_id: selected.id,
                })
            );
        },
    };
    return result;
};

ReceptionScenario.component.data = data;
