/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
 */

/*
    Define states for checkout scenario.
    @param $instance VueJS component instance
*/
export const checkout_states = function ($instance) {
    return {
        select_document: {
            display_info: {
                title: "Choose an order to pack",
                scan_placeholder: () => {
                    if ($instance.state.data.restrict_scan_first) {
                        return "Scan pack / picking / location";
                    }
                    return "Scan pack / product / picking / location";
                },
            },
            on_scan: (scanned) => {
                $instance.wait_call(
                    $instance.odoo.call("scan_document", {barcode: scanned.text})
                );
            },
            on_manual_selection: (evt) => {
                $instance.wait_call($instance.odoo.call("list_stock_picking"));
            },
        },
        manual_selection: {
            display_info: {
                title: "Select a picking and start",
            },
            events: {
                select: "on_select",
                go_back: "on_back",
            },
            on_back: () => {
                $instance.state_to("init");
                $instance.reset_notification();
            },
            on_select: (selected) => {
                $instance.wait_call(
                    $instance.odoo.call("select", {
                        picking_id: selected.id,
                    })
                );
            },
        },
        select_line: {
            display_info: {
                title: "Pick the product by scanning something",
                scan_placeholder: "Scan pack / product / lot / delivery package",
            },
            events: {
                summary: "on_summary",
                select: "on_select",
                back: "on_back",
            },
            on_scan: (scanned) => {
                $instance.wait_call(
                    $instance.odoo.call("scan_line", {
                        picking_id: $instance.state.data.picking.id,
                        barcode: scanned.text,
                        confirm_pack_all:
                            $instance.state.data.need_confirm_pack_all || "",
                        confirm_lot: $instance.state.data.need_confirm_lot,
                    })
                );
            },
            on_select: (selected) => {
                if (!selected) {
                    return;
                }
                $instance.wait_call(
                    $instance.odoo.call("select_line", {
                        picking_id: $instance.state.data.picking.id,
                        move_line_id: selected.id,
                        package_id: _.result(selected, "package_dest.id", false),
                    })
                );
            },
            on_back: () => {
                $instance.state_to("start");
                $instance.reset_notification();
            },
            on_summary: () => {
                $instance.wait_call(
                    $instance.odoo.call("summary", {
                        picking_id: $instance.state.data.picking.id,
                    })
                );
            },
            // FIXME: is not to change qty
            on_edit_package: (pkg) => {
                $instance.state_set_data({package: pkg}, "change_quantity");
                $instance.state_to("change_quantity");
            },
        },
        select_package: {
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
                $instance.wait_call(
                    $instance.odoo
                        .call("scan_package_action", {
                            picking_id: $instance.state.data.picking.id,
                            selected_line_ids: $instance.selectable_line_ids(),
                            barcode: scanned.text,
                        })
                        .then((res) => {
                            $instance.handle_manual_select_highlight_on_scan(res);
                            return res;
                        })
                );
            },
            on_select: (selected) => {
                if (!selected) {
                    return;
                }
                const orig_selected = $instance.selected_line_ids();
                const selected_ids = selected.map(_.property("id"));
                const to_select = _.head(
                    $instance.selectable_lines().filter(function (x) {
                        return (
                            selected_ids.includes(x.id) && !orig_selected.includes(x.id)
                        );
                    })
                );
                const to_unselect = _.head(
                    $instance.selectable_lines().filter(function (x) {
                        return (
                            !selected_ids.includes(x.id) && orig_selected.includes(x.id)
                        );
                    })
                );
                let endpoint, move_line;
                if (to_unselect) {
                    endpoint = "reset_line_qty";
                    move_line = to_unselect;
                } else if (to_select) {
                    endpoint = "set_line_qty";
                    move_line = to_select;
                }
                $instance.wait_call(
                    $instance.odoo.call(endpoint, {
                        picking_id: $instance.state.data.picking.id,
                        selected_line_ids: $instance.selectable_line_ids(),
                        move_line_id: move_line.id,
                    })
                );
            },
            on_qty_edit: (record) => {
                $instance.state_set_data(
                    {
                        picking: $instance.state.data.picking,
                        line: record,
                        selected_line_ids: $instance.selectable_line_ids(),
                    },
                    "change_quantity"
                );
                $instance.state_to("change_quantity");
            },
            on_new_pack: () => {
                $instance.wait_call(
                    $instance.odoo.call("list_delivery_packaging", {
                        picking_id: $instance.state.data.picking.id,
                        selected_line_ids: $instance.selectable_line_ids(),
                    })
                );
            },
            on_existing_pack: () => {
                $instance.wait_call(
                    $instance.odoo.call("list_dest_package", {
                        picking_id: $instance.state.data.picking.id,
                        selected_line_ids: $instance.selectable_line_ids(),
                    })
                );
            },
            on_without_pack: () => {
                $instance.wait_call(
                    $instance.odoo.call("no_package", {
                        picking_id: $instance.state.data.picking.id,
                        selected_line_ids: $instance.selectable_line_ids(),
                    })
                );
            },
            on_back: () => {
                $instance.state_to("select_line");
                $instance.reset_notification();
            },
        },
        select_delivery_packaging: {
            display_info: {
                title: "Select delivery packaging",
                scan_placeholder: "Scan package type",
            },
            events: {
                select: "on_select",
                back: "on_back",
            },
            on_select: (selected) => {
                $instance.state.on_scan({text: selected.barcode});
            },
            on_scan: (scanned) => {
                const picking = $instance.current_doc().record;
                $instance.wait_call(
                    $instance.odoo.call("scan_package_action", {
                        picking_id: picking.id,
                        selected_line_ids: $instance.selected_line_ids(),
                        barcode: scanned.text,
                    })
                );
            },
        },
        change_quantity: {
            display_info: {
                title: "Change quantity",
            },
            events: {
                qty_change_confirm: "on_confirm",
                qty_edit: "on_qty_update",
            },
            on_back: () => {
                $instance.state_to("select_package");
                $instance.reset_notification();
            },
            on_qty_update: (qty) => {
                $instance.state.data.qty = qty;
            },
            on_confirm: () => {
                $instance.wait_call(
                    $instance.odoo.call("set_custom_qty", {
                        picking_id: $instance.state.data.picking.id,
                        selected_line_ids: $instance.selectable_line_ids(),
                        move_line_id: $instance.state.data.line.id,
                        qty_done: $instance.state.data.qty,
                    })
                );
            },
        },
        select_dest_package: {
            display_info: {
                title: "Select destination package",
            },
            events: {
                select: "on_select",
                back: "on_back",
            },
            on_scan: (scanned) => {
                $instance.wait_call(
                    $instance.odoo.call("scan_dest_package", {
                        picking_id: $instance.state.data.picking.id,
                        selected_line_ids: $instance.selected_line_ids(),
                        barcode: scanned.text,
                    })
                );
            },
            on_select: (selected) => {
                if (!selected) {
                    return;
                }
                $instance.wait_call(
                    $instance.odoo.call("set_dest_package", {
                        picking_id: $instance.state.data.picking.id,
                        selected_line_ids: $instance.selected_line_ids(),
                        package_id: selected.id,
                    })
                );
            },
            on_back: () => {
                $instance.state_to("select_package");
                $instance.reset_notification();
            },
        },
        summary: {
            display_info: {
                title: "Summary",
            },
            events: {
                select: "on_select",
                back: "on_back",
                cancel_picking_line: "on_cancel",
                pkg_change_type: "on_pkg_change_type",
                mark_as_done: "on_mark_as_done",
                continue: "on_continue",
            },
            on_back: () => {
                $instance.state_to("start");
                $instance.reset_notification();
            },
            on_pkg_change_type: (pkg) => {
                $instance.wait_call(
                    $instance.odoo.call("list_packaging", {
                        picking_id: $instance.state.data.picking.id,
                        package_id: pkg.id,
                    })
                );
            },
            on_cancel: (data) => {
                $instance.wait_call(
                    $instance.odoo.call("cancel_line", {
                        picking_id: $instance.state.data.picking.id,
                        // We get either line_id or package_id
                        package_id: data.package_id,
                        line_id: data.line_id,
                    })
                );
            },
            on_mark_as_done: () => {
                $instance.wait_call(
                    $instance.odoo.call("done", {
                        picking_id: $instance.state.data.picking.id,
                    })
                );
            },
            on_continue: () => {
                $instance.wait_call(
                    $instance.odoo.call("select", {
                        picking_id: $instance.state.data.picking.id,
                    })
                );
            },
        },
        change_packaging: {
            display_info: {
                title: "Change packaging",
            },
            events: {
                select: "on_select",
            },
            on_select: (selected) => {
                if (!selected) {
                    return;
                }
                $instance.wait_call(
                    $instance.odoo.call("set_packaging", {
                        picking_id: $instance.state.data.picking.id,
                        package_id: $instance.state.data.package.id,
                        packaging_id: selected.id,
                    })
                );
            },
        },
        confirm_done: {
            display_info: {
                title: "Confirm done",
            },
            events: {
                go_back: "on_back",
            },
            on_confirm: () => {
                $instance.wait_call(
                    $instance.odoo.call("done", {
                        picking_id: $instance.state.data.picking.id,
                        confirmation: true,
                    })
                );
            },
            on_back: () => {
                $instance.state_to("summary");
                $instance.reset_notification();
            },
        },
        select_child_location: {
            display_info: {
                title: "Set destination location",
                scan_placeholder: "Scan location",
            },
            events: {
                go_back: "on_back",
            },
            on_scan: (scanned) => {
                $instance.wait_call(
                    $instance.odoo.call("scan_dest_location", {
                        picking_id: $instance.state.data.picking.id,
                        barcode: scanned.text,
                    })
                );
            },
            on_back: () => {
                $instance.state_to("summary");
                $instance.reset_notification();
            },
        },
    };
};
