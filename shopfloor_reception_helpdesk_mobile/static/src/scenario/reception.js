/**
 * Copyright 2025 ACSONE SA/NV (https://acsone.eu)
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
 */

import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

const reception_scenario = process_registry.get("reception");
const _get_states = reception_scenario.component.methods._get_states;
// Get the original template of the reception scenario
const template = reception_scenario.component.template;
// And inject the new state template (for this module) into it
const pos = template.indexOf("</Screen>");
const new_template =
    template.substring(0, pos) +
    `
 <template v-if="state_is('set_destination')">
    <div v-if="state.data.picking.helpdesk_ticket_allowed" class="button-list button-vertical-list full">
        <v-row align="center">
            <v-col class="text-center" cols="12">
                <btn-action @click="state.on_declare_helpdesk"><v-icon>mdi-lifebuoy</v-icon>Helpdesk</btn-action>
            </v-col>
        </v-row>
    </div>

 </template>

 <template v-if="state_is('start_helpdesk')">
    <v-text-field label="Description" placeholder="Ticket Description" class="current-value" v-model="state.data.helpdesk_wizard.description" />
        <v-combobox
            label="Motive"
            :items="state.data.available_motives"
            item-text="name"
            v-model="state.data.helpdesk_wizard.motive"
        ></v-combobox>
    <div class="button-list button-vertical-list full">
        <v-row align="center">
            <v-col class="text-center" cols="12">
                <btn-action @click="state.on_create_helpdesk">Create Helpdesk Ticket</btn-action>
            </v-col>
            <v-col class="text-center" cols="12">
                <btn-back />
            </v-col>
        </v-row>
    </div>

 </template>

` +
    template.substring(pos);

// Extend the reception scenario with :
//   - the new patched template
//   - the js code for the new state
const ReceptionHelpdesk = process_registry.extend("reception", {
    template: new_template,
    props: ["helpdesk_description"],
    "methods._get_states": function () {
        let states = _get_states.bind(this)();
        const set_destination = states.set_destination;

        const self = this;
        set_destination.on_declare_helpdesk = function () {
            self.wait_call(
                self.odoo.call("start_helpdesk", {
                    picking_id: self.state.data.picking.id,
                    selected_line_id: self.state.data.selected_move_line[0].id,
                })
            );
        };

        states["start_helpdesk"] = {
            on_create_helpdesk: () => {
                const motive = self.state.data.helpdesk_wizard.motive;
                self.wait_call(
                    self.odoo.call("create_helpdesk", {
                        picking_id: self.state.data.picking.id,
                        selected_line_id: self.state.data.selected_move_line[0].id,
                        helpdesk_wizard_id: self.state.data.helpdesk_wizard.id,
                        description: self.state.data.helpdesk_wizard.description,
                        motive_id: motive ? motive.id : false,
                    })
                );
            },
        };
        return states;
    },
});

process_registry.replace("reception", ReceptionHelpdesk);
