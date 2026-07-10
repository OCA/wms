/**
 * Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

const reception_scenario = process_registry.get("reception");
// Get the original template of the reception scenario
const template = reception_scenario.component.template;
// And inject the new state template (for this module) into it
const pos = template.indexOf("</Screen>");
let new_template =
    template.substring(0, pos) +
    `
 <div v-if="state_is('create_new_packaging')">

     <v-form ref="new_packaging_form">
        <v-container>
            <v-row>
                <v-text-field
                    label="Name"
                    placeholder="Packaging Name"
                    v-model="state.data.packaging_name"
                    :rules="[v => !!v || 'Name is required']"
                ></v-text-field>
            </v-row>
            <v-row>
                <v-text-field
                    label="Quantiy"
                    type="number"
                    placeholder="Packaging Quantity"
                    v-model="state.data.packaging_quantity"
                    :rules="[v => !!v || 'Quantity is required']"
                ></v-text-field>
            </v-row>
            <v-combobox
                label="Packaging Level"
                clearable
                :items="state.data.packaging_levels"
                item-text="name"
                v-model="state.data.packaging_level"
            />
       </v-container>
    </v-form>

    <div class="button-list button-vertical-list full">
        <v-row align="center">
            <v-col class="text-center" cols="12">
                <btn-action action="todo" @click="state.on_create" :disabled="disable_create_new_packaging_button">Create</btn-action>
            </v-col>
        </v-row>
        <v-row align="center">
            <v-col class="text-center" cols="12">
                <btn-back/>
            </v-col>
        </v-row>
    </div>
</div>

` +
    template.substring(pos);

// Add button to create new packaging in 'set_quantity' screen
const regex = /<v-row\b[^>]*v-if="show_without_pack_actions"[^>]*>[\s\S]*?<\/v-row>/;
const match = regex.exec(template);

if (match) {
    const insertIndex = match.index + match[0].length;

    new_template =
        new_template.substring(0, insertIndex) +
        `
        <v-row v-if="show_create_new_packaging_button">
            <v-col class="text-center" cols="12">
                <btn-action color="warning" @click="state.create_new_packaging">
                    Create New Packaging
                </btn-action>
            </v-col>
        </v-row>
            ` +
        new_template.substring(insertIndex);
}

// Extend the reception scenario with :
//   - the new patched template
//   - the js code for the new state
const _get_states_base = reception_scenario.component.methods._get_states;
const ReceptionAddPackaging = process_registry.extend("reception", {
    template: new_template,
    computed: {
        ...(reception_scenario.component.computed || {}),
        show_create_new_packaging_button: function () {
            const create_new_packaging = this.state.data.create_new_packaging;
            if (!create_new_packaging) return false;
            return create_new_packaging;
        },
        disable_create_new_packaging_button: function () {
            const data = this.state.data;
            return !(
                data.packaging_name &&
                data.packaging_quantity &&
                data.packaging_level
            );
        },
    },
    methods: {
        ...(reception_scenario.component.methods || {}),
        _get_states: function () {
            let states = _get_states_base.bind(this)();

            // Capture 'this' in a variable to be safe across async boundaries
            const self = this;

            states["set_quantity"] = {
                ...states["set_quantity"],
                create_new_packaging: function () {
                    self.wait_call(
                        self.odoo.call("start_new_packaging", {
                            picking_id: self.state.data.picking.id,
                            selected_line_id: self.state.data.selected_move_line[0].id,
                        })
                    );
                },
            };
            states["create_new_packaging"] = {
                display_info: {
                    title: "Create new packaging",
                },
                on_create: function () {
                    self.wait_call(
                        self.odoo.call("create_new_packaging", {
                            picking_id: self.state.data.picking.id,
                            selected_line_id: self.state.data.selected_move_line.id,
                            name: self.state.data.packaging_name,
                            quantity: self.state.data.packaging_quantity,
                            packaging_level_id: self.state.data.packaging_level.id,
                        })
                    );
                },
            };
            return states;
        },
    },
});

process_registry.replace("reception", ReceptionAddPackaging);
