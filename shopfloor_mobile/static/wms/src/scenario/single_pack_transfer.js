/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Raphaël Reverdy <raphael.reverdy@akretion.com>
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ScenarioBaseMixin} from "/shopfloor_mobile_base/static/wms/src/scenario/mixins.js";
import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

export var SinglePackStatesMixin = {
    data: function () {
        return {
            states: {
                // Generic state for when to start w/ scanning a pack or loc
                start: {
                    display_info: {
                        title: "Start by scanning a pack or a location",
                        scan_placeholder: "Scan pack",
                    },
                    on_scan: (scanned) => {
                        const data = this.state.data;
                        this.wait_call(
                            this.odoo.call("start", {
                                barcode: scanned.text,
                                confirmation: data.confirmation_required || "",
                            })
                        );
                    },
                },
                scan_location: {
                    display_info: {
                        title: "Set a location",
                        scan_placeholder: "Scan location",
                        show_cancel_button: true,
                    },
                    on_scan: (scanned, confirmation = false) => {
                        const data = this.state.data;
                        this.state_set_data({location_barcode: scanned.text});
                        this.wait_call(
                            this.odoo.call("validate", {
                                package_level_id: data.id,
                                location_barcode: scanned.text,
                                confirmation:
                                    confirmation || data.confirmation_required || "",
                            })
                        );
                    },
                    on_cancel: () => {
                        this.wait_call(
                            this.odoo.call("cancel", {
                                package_level_id: this.state.data.id,
                            })
                        );
                    },
                },
            },
        };
    },
};

// TODO: consider replacing the dynamic "autofocus" in the searchbar by an event.
// At the moment, we need autofocus to be disabled if there's a user popup.
const SinglePackTransfer = {
    mixins: [ScenarioBaseMixin, SinglePackStatesMixin],
    template: `
        <Screen :screen_info="screen_info">
            <template v-slot:header>
                <state-display-info :info="state.display_info" v-if="state.display_info"/>
            </template>
            <searchbar
                v-if="state_is(initial_state_key)"
                v-on:found="on_scan"
                :autofocus="!screen_info.user_popup"
                :input_placeholder="search_input_placeholder"
            ></searchbar>
            <searchbar
                v-if="state_is('scan_location')"
                v-on:found="on_scan"
                :autofocus="!screen_info.user_popup"
                :input_placeholder="search_input_placeholder"
                :input_data_type="'location'"
            ></searchbar>
            <div v-if="state.key != 'show_completion_info' && _.result(state, 'data.picking')">
                <item-detail-card
                    :key="make_state_component_key(['package', state.data.id])"
                    :record="state.data"
                    :card_color="utils.colors.color_for('screen_step_done')"
                >
                    <template v-slot:after_details>
                        <v-card-subtitle class="pb-0">
                            <span class="font-weight-bold">Weight:</span>
                            <span>
                                {{ _get_pack_weight() }}
                            </span>
                        </v-card-subtitle>
                        <v-card-text class="details pt-0">
                            <div v-for="product in state.data.products" class="field-detail pt-2">
                                <div>
                                    <span class="font-weight-bold">Product:</span>
                                        <span>
                                            {{ product.display_name }}
                                        </span>
                                    </span>
                                </div>
                                <div class='ml-2'>
                                    <span class="font-weight-bold">Vendor code:</span>
                                        <span>
                                            {{ product.supplier_code }}
                                        </span>
                                    </span>
                                </div>
                            </div>
                        </v-card-text>
                    </template>
                </item-detail-card>
                <item-detail-card
                    :key="make_state_component_key(['destination', state.data.id])"
                    :record="state.data"
                    :options="{main: true, key_title: 'location_dest.name', title_action_field:  {action_val_path: 'location_dest.barcode'}}"
                    :card_color="utils.colors.color_for('screen_step_todo')"
                />
            </div>
            <last-operation v-if="state_is('show_completion_info')" v-on:confirm="state.on_confirm"></last-operation>
            <cancel-button v-on:cancel="on_cancel" v-if="show_cancel_button"></cancel-button>
        </Screen>
    `,
    data: function () {
        return {
            usage: "single_pack_transfer",
            show_reset_button: true,
            initial_state_key: "start",
            states: {
                show_completion_info: {
                    on_confirm: () => {
                        // TODO: turn the cone?
                        this.state_to("start");
                    },
                },
            },
        };
    },
    methods: {
        _get_pack_weight: function () {
            let weight = this.state.data.weight;
            let uom = this.state.data.weight_uom;
            if (!weight) {
                weight = this.state.data.estimated_weight_kg;
                uom = "kg";
            }
            return weight.toFixed(3) + " " + uom;
        },
    },
};
process_registry.add("single_pack_transfer", SinglePackTransfer);

export default SinglePackTransfer;
