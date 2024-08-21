/**
 * Copyright 2021 ACSONE SA/NV
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

const registry_key = "cluster_picking";
const ClusterPickingBase = process_registry.get(registry_key);

let template = ClusterPickingBase.component.template;
ClusterPickingBase.component.template = template.replace(
    "</Screen>",
    `
    <pack-picking-detail
         v-if="state_is('pack_picking_scan_pack')"
         :record="state.data"
    />
    <pack-picking-detail
         v-if="state_is('pack_picking_put_in_pack')"
         :record="state.data"
    />
    <div v-if="state_is('select_package')">
        <v-alert type="info" tile v-if="state.data.packing_info" class="packing-info">
             <p v-text="state.data.packing_info" />
         </v-alert>
        <item-detail-card
            v-if="state.data.picking.carrier"
            :key="make_state_component_key(['picking-carrier', state.data.picking.id])"
            :record="state.data.picking.carrier"
            :options="{main: true, key_title: 'name', title_icon: 'mdi-truck-outline'}"
            />
        <detail-picking-select
            :record="state.data.picking"
            :select_records="state.data.selected_move_lines"
            :select_options="select_package_manual_select_opts()"
            :key="make_state_component_key(['detail-picking-select'])"
            />
        <div class="button-list button-vertical-list full">
            <!-- TODO:<v-row align="center" v-if="state.data.package_allowed">
                <v-col class="text-center" cols="12">
                    <btn-action
                            @click="state.on_existing_pack"
                            :disabled="_.isEmpty(selected_lines())"
                            >Existing pack</btn-action>
                </v-col>
            </v-row>-->
            <v-row align="center" v-if="state.data.package_allowed">
                <v-col class="text-center" cols="12">
                    <btn-action
                            @click="state.on_new_pack"
                            :disabled="_.isEmpty(selected_lines())"
                            >New pack</btn-action>
                </v-col>
            </v-row>
            <v-row align="center" v-if="state.data.no_package_enabled">
                <v-col class="text-center" cols="12">
                    <btn-action
                            @click="state.on_without_pack"
                            :disabled="_.isEmpty(selected_lines())"
                            >Process w/o pack</btn-action>
                </v-col>
            </v-row>
        </div>
    </div>
    <div v-if="state_is('select_delivery_packaging')">

        <manual-select
            :records="state.data.packaging"
            :options="select_delivery_packaging_manual_select_options()"
            :key="make_state_component_key(['cluster_picking', 'select-delivery-packaging'])"
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

// Keep the pointer to the orginal method
let data_result_method = ClusterPickingBase.component.data;

ClusterPickingBase.component.computed.searchbar_input_type = function () {
    if (this.state_is("pack_picking_put_in_pack")) {
        return "number";
    }
    return "text";
};

ClusterPickingBase.component.computed.existing_package_select_fields = function () {
    return [
        {path: "weight"},
        {path: "move_line_count", label: "Line count"},
        {path: "packaging.name"},
    ];
};

ClusterPickingBase.component.methods.select_package_manual_select_opts = function () {
    return {
        multiple: true,
        initValue: this.selected_line_ids(),
        card_klass: "loud-labels",
        list_item_component: "picking-select-package-content",
        list_item_options: {actions: ["action_qty_edit"]},
    };
};

ClusterPickingBase.component.methods.select_delivery_packaging_manual_select_options =
    function () {
        return {
            showActions: false,
        };
    };

ClusterPickingBase.component.methods.selected_line_ids = function () {
    return this.selected_lines().map(_.property("id"));
};

ClusterPickingBase.component.methods.selectable_lines = function () {
    const stored = this.state_get_data("select_package");
    return _.result(stored, "selected_move_lines", []);
};

ClusterPickingBase.component.methods.selectable_line_ids = function () {
    return this.selectable_lines().map(_.property("id"));
};

ClusterPickingBase.component.methods.selected_lines = function () {
    return this.selectable_lines().filter(function (x) {
        return x.qty_done > 0;
    });
};

// Replace the data method with our new method to add
// our new state
let component = ClusterPickingBase.component;
let data = function () {
    // we must bin the original method to this to put it into
    // the object context
    let result = data_result_method.bind(this)();
    // add our new state
    result.states.pack_picking_put_in_pack = {
        display_info: {
            title: this.$t("cluster_picking.pack_picking_put_in_pack.title"),
            scan_placeholder: this.$t(
                "cluster_picking.pack_picking_put_in_pack.scan_placeholder"
            ),
        },
        on_scan: (scanned) => {
            let endpoint, endpoint_data;
            const data = this.state.data;
            endpoint = "put_in_pack";
            endpoint_data = {
                picking_batch_id: this.current_batch().id,
                picking_id: data.id,
                nbr_packages: parseInt(scanned.text, 10),
            };
            this.wait_call(this.odoo.call(endpoint, endpoint_data));
        },
    };
    result.states.pack_picking_scan_pack = {
        display_info: {
            title: this.$t("cluster_picking.pack_picking_scan_pack.title"),
            scan_placeholder: this.$t(
                "cluster_picking.pack_picking_scan_pack.scan_placeholder"
            ),
        },
        on_scan: (scanned) => {
            let endpoint, endpoint_data;
            const data = this.state.data;
            endpoint = "scan_packing_to_pack";
            endpoint_data = {
                picking_batch_id: this.current_batch().id,
                picking_id: data.id,
                barcode: scanned.text,
            };
            this.wait_call(this.odoo.call(endpoint, endpoint_data));
        },
    };
    result.states.select_package = {
        // TODO: /set_line_qty is not handled yet
        // because is not clear how to handle line selection
        // and qty set.
        // ATM given that manual-select uses v-list-item-group
        // when you touch a line you select/unselect it
        // which means we cannot rely on this to go to edit.
        // If we need it, we have to change manual-select
        // to use pure list + checkboxes.
        display_info: {
            title: "Select package",
            scan_placeholder: "Scan existing package / package type",
        },
        events: {
            qty_edit: "on_qty_edit",
            select: "on_select",
            back: "on_back",
        },
        on_scan: (scanned) => {
            this.wait_call(
                this.odoo.call("scan_package_action", {
                    picking_id: this.state.data.picking.id,
                    selected_line_ids: this.selectable_line_ids(),
                    barcode: scanned.text,
                })
            );
        },
        on_select: (selected) => {
            return;
            // TODO:
            // if (!selected) {
            //     return;
            // }
            // const orig_selected = $instance.selected_line_ids();
            // const selected_ids = selected.map(_.property("id"));
            // const to_select = _.head(
            //     $instance.selectable_lines().filter(function (x) {
            //         return selected_ids.includes(x.id) && !orig_selected.includes(x.id);
            //     })
            // );
            // const to_unselect = _.head(
            //     $instance.selectable_lines().filter(function (x) {
            //         return !selected_ids.includes(x.id) && orig_selected.includes(x.id);
            //     })
            // );
            // let endpoint, move_line;
            // if (to_unselect) {
            //     endpoint = "reset_line_qty";
            //     move_line = to_unselect;
            // } else if (to_select) {
            //     endpoint = "set_line_qty";
            //     move_line = to_select;
            // }
            // $instance.wait_call(
            //     $instance.odoo.call(endpoint, {
            //         picking_id: $instance.state.data.picking.id,
            //         selected_line_ids: $instance.selectable_line_ids(),
            //         move_line_id: move_line.id,
            //     })
            // );
        },
        on_qty_edit: (record) => {
            return;
            // TODO:
            // $instance.state_set_data(
            //     {
            //         picking: $instance.state.data.picking,
            //         line: record,
            //         selected_line_ids: $instance.selectable_line_ids(),
            //     },
            //     "change_quantity"
            // );
            // $instance.state_to("change_quantity");
        },
        on_new_pack: () => {
            /**
             * Trigger the call to list delivery packaging types
             * as user wants to put porducts in a new pack.
             */
            let endpoint, endpoint_data;
            const data = this.state.data;
            endpoint = "list_delivery_packaging";
            endpoint_data = {
                picking_batch_id: this.current_batch().id,
                picking_id: data.picking.id,
                selected_line_ids: this.selectable_line_ids(),
            };
            this.wait_call(this.odoo.call(endpoint, endpoint_data));
        },
        on_existing_pack: () => {
            return;
            // TODO:
            // $instance.wait_call(
            //     $instance.odoo.call("list_dest_package", {
            //         picking_id: $instance.state.data.picking.id,
            //         selected_line_ids: $instance.selectable_line_ids(),
            //     })
            // );
        },
        on_without_pack: () => {
            return;
            // TODO:
            // $instance.wait_call(
            //     $instance.odoo.call("no_package", {
            //         picking_id: $instance.state.data.picking.id,
            //         selected_line_ids: $instance.selectable_line_ids(),
            //     })
            // );
        },
        on_back: () => {
            $instance.state_to("select_line");
            $instance.reset_notification();
        },
    };
    result.states.select_delivery_packaging = {
        /**
         * This will catch user events when selecting the delivery packaging type
         * from:
         *   - the scanned barcode
         *   - the direct selection on screen
         */
        display_info: {
            title: "Select delivery packaging or scan it",
            scan_placeholder: "Scan package type",
        },
        events: {
            select: "on_select",
            back: "on_back",
        },
        on_select: (selected) => {
            const picking = this.current_doc().record;
            const data = this.state.data.picking;
            this.wait_call(
                this.odoo.call("put_in_pack", {
                    picking_batch_id: this.current_batch().id,
                    picking_id: data.id,
                    selected_line_ids: this.selected_line_ids(),
                    package_type_id: selected.id,
                })
            );
        },
        on_scan: (scanned) => {
            const picking = this.current_doc().record;
            const data = this.state.data;
            this.wait_call(
                this.odoo.call("scan_package_action", {
                    picking_id: data.id,
                    selected_line_ids: this.selected_line_ids(),
                    barcode: scanned.text,
                })
            );
        },
    };

    return result;
};

ClusterPickingBase.component.data = data;
