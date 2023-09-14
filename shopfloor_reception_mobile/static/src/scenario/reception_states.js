/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
 */

/*
    Define states for reception scenario.
    @param this VueJS component instance
*/
export const reception_states = function () {
    return {
        init: {
            enter: () => {
                this.wait_call(this.odoo.call("start"));
            },
        },
        select_document: {
            display_info: {
                title: "Choose an operation",
                scan_placeholder: "Scan document / product / package",
            },
            events: {
                select: "on_select",
            },
            on_select: (selected) => {
                this.wait_call(
                    this.odoo.call("scan_document", {
                        barcode: selected.name,
                    })
                );
            },
            on_scan: (barcode) => {
                this.wait_call(
                    this.odoo.call("scan_document", {
                        barcode: barcode.text,
                    })
                );
            },
            on_manual_selection: () => {
                this.wait_call(this.odoo.call("list_stock_pickings"));
            },
        },
        manual_selection: {
            title: "Choose an operation",
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
        },
        select_move: {
            display_info: {
                title: "Select a move",
                scan_placeholder: "Scan product / package",
            },
            events: {
                cancel_picking_line: "on_cancel",
                select: "on_select",
            },
            on_scan: (barcode) => {
                this.wait_call(
                    this.odoo.call("scan_line", {
                        picking_id: this.state.data.picking.id,
                        barcode: barcode.text,
                    })
                );
            },
            on_mark_as_done: () => {
                this.wait_call(
                    this.odoo.call("done_action", {
                        picking_id: this.state.data.picking.id,
                    })
                );
            },
            on_select: (selected) => {
                this.wait_call(
                    this.odoo.call("manual_select_move", {
                        move_id: selected.id,
                    })
                );
            },
            on_cancel: () => {
                // TODO: this endpoing is currently missing in the backend,
                // and it's currently in the roadmap.
                // Once it's implemented, uncomment this call.
                // this.wait_call(
                //     this.odoo.call("cancel", {
                //         package_level_id: this.state.data.id,
                //     })
                // );
            },
        },
        confirm_done: {
            display_info: {
                title: "Confirm done",
            },
            events: {
                confirm: "on_confirm",
                go_back: "on_back",
            },
            on_confirm: () => {
                this.wait_call(
                    this.odoo.call("done_action", {
                        picking_id: this.state.data.picking.id,
                        confirmation: true,
                    })
                );
            },
            on_back: () => {
                this.state_to("select_move");
                this.reset_notification();
            },
        },
        set_lot: {
            display_info: {
                title: "Set lot",
                scan_placeholder: "Scan lot",
                scan_input_placeholder_expiry: "Scan expiration date",
            },
            on_scan: (barcode) => {
                // Scan a lot
                this.wait_call(
                    this.odoo.call("set_lot", {
                        picking_id: this.state.data.picking.id,
                        selected_line_id: this.line_being_handled.id,
                        lot_name: barcode.text,
                    })
                ).then(() => {
                    // We need to wait for the call to the backend to be over
                    // to update the date-picker-input component
                    // with the expiration_date of the selected lot.
                    event_hub.$emit("datepicker:newdate", this.line_being_handled.lot);
                });
            },
            on_date_picker_selected: (expiration_date) => {
                // Select expiration_date
                this.wait_call(
                    this.odoo.call("set_lot", {
                        picking_id: this.state.data.picking.id,
                        selected_line_id: this.line_being_handled.id,
                        expiration_date: expiration_date,
                    })
                );
            },
            on_confirm_action: () => {
                this.wait_call(
                    this.odoo.call("set_lot_confirm_action", {
                        picking_id: this.state.data.picking.id,
                        selected_line_id: this.line_being_handled.id,
                    })
                );
            },
        },
        set_quantity: {
            display_info: {
                title: "Set quantity",
                scan_placeholder: "Scan document / product / package / location",
            },
            events: {
                qty_edit: "on_qty_edit",
                go_back: "on_back",
                cancel: "on_cancel",
            },
            on_qty_edit: (qty) => {
                this.scan_destination_qty = parseInt(qty, 10);
            },
            on_scan: (barcode) => {
                this.wait_call(
                    this.odoo.call("set_quantity", {
                        // TODO: add quantity from qty-picker
                        picking_id: this.state.data.picking.id,
                        selected_line_id: this.line_being_handled.id,
                        quantity: this.scan_destination_qty,
                        barcode: barcode.text,
                        confirmation: this.state.data.confirmation_required || "",
                    })
                );
            },
            on_cancel: () => {
                this.wait_call(
                    this.odoo.call("set_quantity__cancel_action", {
                        picking_id: this.state.data.picking.id,
                        selected_line_id: this.line_being_handled.id,
                    })
                );
            },
            on_add_to_existing_pack: () => {
                this.wait_call(
                    this.odoo.call("process_with_existing_pack", {
                        picking_id: this.state.data.picking.id,
                        selected_line_id: this.line_being_handled.id,
                        quantity: this.scan_destination_qty,
                    })
                );
            },
            on_create_new_pack: () => {
                this.wait_call(
                    this.odoo.call("process_with_new_pack", {
                        picking_id: this.state.data.picking.id,
                        selected_line_id: this.line_being_handled.id,
                        quantity: this.scan_destination_qty,
                    })
                );
            },
            on_process_without_pack: () => {
                this.wait_call(
                    this.odoo.call("process_without_pack", {
                        picking_id: this.state.data.picking.id,
                        selected_line_id: this.line_being_handled.id,
                        quantity: this.scan_destination_qty,
                    })
                );
            },
            on_back: () => {
                this.state_to("select_move");
                this.reset_notification();
            },
        },
        set_destination: {
            display_info: {
                title: "Set destination",
                scan_placeholder: "Scan destination location",
            },
            on_scan: (location) => {
                this.wait_call(
                    this.odoo.call("set_destination", {
                        picking_id: this.state.data.picking.id,
                        selected_line_id: this.line_being_handled.id,
                        location_name: location.text,
                        // FIXME if it is always set to true, it is not really used ?
                        confirmation: true,
                    })
                );
            },
        },
        select_dest_package: {
            display_info: {
                title: "Select destination package",
                scan_placeholder: "Scan destination package",
            },
            events: {
                select: "on_select",
            },
            on_scan: (barcode) => {
                this.wait_call(
                    this.odoo.call("select_dest_package", {
                        picking_id: this.state.data.picking.id,
                        selected_line_id: this.line_being_handled.id,
                        barcode: barcode.text,
                    })
                );
            },
            on_select: (selected) => {
                this.wait_call(
                    this.odoo.call("select_dest_package", {
                        picking_id: this.state.data.picking.id,
                        selected_line_id: this.line_being_handled.id,
                        barcode: selected.name,
                    })
                );
            },
        },
        confirm_new_package: {
            display_info: {
                title: "Confirm new package",
            },
            events: {
                confirm: "on_confirm",
                go_back: "on_back",
            },
            on_confirm: () => {
                this.wait_call(
                    this.odoo.call("select_dest_package", {
                        picking_id: this.state.data.picking.id,
                        selected_line_id: this.line_being_handled.id,
                        confirmation: true,
                        barcode: this.state.data.new_package_name,
                    })
                );
            },
            on_back: () => {
                this.state_to("select_dest_package");
                this.reset_notification();
            },
        },
    };
};
