/**
- Copyright 2025 ACSONE SA/NV (https://acsone.eu)
- License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
 */

import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

const reception_scenario = process_registry.get("reception");

const ReceptionBackorderReason = process_registry.extend("reception", {
    template: reception_scenario.component.template.replace(
        "</Screen>",
        `
        <template v-if="state_is('choose_backorder_reason')">
            <manual-select
                :records="state.data.backorder_reasons"
                :key="make_state_component_key(['reception', 'select-backorder-reason'])"
                :options="manual_select_options_for_choose_backorder_reason()"
                @select="state.on_select"
            />
            <div class="button-list button-vertical-list full">
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <btn-back />
                    </v-col>
                </v-row>
            </div>
        </template>
    </Screen>`
    ),
    methods: {
        ...(reception_scenario.component.methods || {}),
        backorder_reason_fields: function () {
            return [
                {
                    path: "backorder_action_to_do.label",
                    label: this.$t("reception.choose_backorder_reason.field.action"),
                },
            ];
        },
        manual_select_options_for_choose_backorder_reason: function () {
            return {
                list_item_options: {
                    key_title: "name",
                    loud_title: true,
                    fields: this.backorder_reason_fields(),
                },
            };
        },
        _get_states: function () {
            const _get_states_base = reception_scenario.component.methods._get_states;
            const states = _get_states_base.bind(this)();

            // Capture 'this' in a variable to be safe across async boundaries
            const self = this;

            states.choose_backorder_reason = {
                display_info: {
                    title: this.$t("reception.choose_backorder_reason.title"),
                },
                on_select: (selected) => {
                    self.wait_call(
                        self.odoo.call("choose_backorder_reason", {
                            picking_id: self.state.data.picking.id,
                            reason_id: selected.id,
                        })
                    );
                },
            };

            return states;
        },
    },
});

process_registry.replace("reception", ReceptionBackorderReason);
