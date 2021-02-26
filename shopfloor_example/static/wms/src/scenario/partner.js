/**
 * Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ScenarioBaseMixin} from "/shopfloor_mobile_base/static/wms/src/scenario/mixins.js";
import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

const Partner = {
    mixins: [ScenarioBaseMixin],
    template: `
        <Screen :screen_info="screen_info">
            <template v-slot:header>
                <state-display-info :info="state.display_info" v-if="state.display_info"/>
            </template>
            <searchbar
                v-if="state.on_scan"
                v-on:found="on_scan"
                :input_placeholder="search_input_placeholder"
                />
            <div v-if="state_is('listing')">
                <manual-select
                    :records="state.data.records"
                    :key="make_state_component_key(['manual-select'])"
                    :options="{showActions: false}"
                    />
            </div>
            <div v-if="state_is('detail')">
                <detail-partner_example :record="state.data.record" />
            </div>
            <div class="button-list button-vertical-list full">
                <v-row align="center" v-if="state_in(['scan', 'detail'])">
                    <v-col class="text-center" cols="12">
                        <btn-action @click="state.on_manual_selection">Manual selection</btn-action>
                    </v-col>
                </v-row>
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <btn-back />
                    </v-col>
                </v-row>
            </div>
        </Screen>
        `,
    methods: {
        current_doc: function() {
            const data = this.state_get_data("view_partner");
            if (_.isEmpty(data)) {
                return null;
            }
            return {
                record: data.picking,
                identifier: data.picking.name,
            };
        },
    },
    data: function() {
        return {
            usage: "partner_example",
            initial_state_key: "scan",
            states: {
                scan: {
                    display_info: {
                        title: "Scan a partner",
                        scan_placeholder: "Scan ref",
                    },
                    on_scan: scanned => {
                        this.wait_call(this.odoo.get(["scan", scanned.text]));
                    },
                    on_manual_selection: evt => {
                        this.wait_call(this.odoo.get("partner_list"));
                    },
                },
                detail: {
                    display_info: {
                        title: "Partner detail",
                    },
                    on_scan: scanned => {
                        this.wait_call(this.odoo.get(["scan", scanned.text]));
                    },
                    on_manual_selection: evt => {
                        this.wait_call(this.odoo.get("partner_list"));
                    },
                },
                listing: {
                    display_info: {
                        title: "Select partner",
                    },
                    events: {
                        select: "on_select",
                    },
                    on_select: selected => {
                        if (selected)
                            this.wait_call(this.odoo.get(["detail", selected.id]));
                    },
                },
            },
        };
    },
};

process_registry.add("partner_example", Partner);

export default Partner;
