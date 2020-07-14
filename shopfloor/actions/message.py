from odoo import _

from odoo.addons.component.core import Component


class MessageAction(Component):
    """Provide message templates

    The methods should be used in Service Components, in order to share as much
    as possible the messages for similar events.

    Before adding a message, please look if no message already exists,
    and consider making an existing message more generic.
    """

    _name = "shopfloor.message.action"
    _inherit = "shopfloor.process.action"
    _usage = "message"

    def no_picking_type(self):
        return {
            "message_type": "error",
            "body": _("No operation type found for this menu and profile."),
        }

    def several_picking_types(self):
        return {
            "message_type": "error",
            "body": _("Several operation types found for this menu and profile."),
        }

    def package_not_found_for_barcode(self, barcode):
        return {
            "message_type": "error",
            "body": _("The package %s doesn't exist") % barcode,
        }

    def bin_not_found_for_barcode(self, barcode):
        return {"message_type": "error", "body": _("Bin %s doesn't exist") % barcode}

    def package_not_allowed_in_src_location(self, barcode, picking_types):
        return {
            "message_type": "error",
            "body": _("You cannot work on a package (%s) outside of locations: %s")
            % (
                barcode,
                ", ".join(picking_types.mapped("default_location_src_id.name")),
            ),
        }

    def already_running_ask_confirmation(self):
        return {
            "message_type": "warning",
            "body": _("Operation's already running. Would you like to take it over?"),
        }

    def scan_destination(self):
        return {"message_type": "info", "body": _("Scan the destination location")}

    def scan_lot_on_product_tracked_by_lot(self):
        return {
            "message_type": "warning",
            "body": _("Product tracked by lot, please scan one."),
        }

    def operation_not_found(self):
        return {
            "message_type": "error",
            "body": _("This operation does not exist anymore."),
        }

    def stock_picking_not_found(self):
        return {
            "message_type": "error",
            "body": _("This transfer does not exist anymore."),
        }

    def package_not_found(self):
        return {
            "message_type": "error",
            "body": _("This package does not exist anymore."),
        }

    def package_not_available_in_picking(self, package, picking):
        return {
            "message_type": "warning",
            "body": _("Package {} is not available in transfer {}.").format(
                package.name, picking.name
            ),
        }

    def line_not_available_in_picking(self, picking):
        return {
            "message_type": "warning",
            "body": _("This line is not available in transfer {}.").format(
                picking.name
            ),
        }

    def record_not_found(self):
        return {
            "message_type": "error",
            "body": _("The record you were working on does not exist anymore."),
        }

    def barcode_not_found(self):
        return {"message_type": "error", "body": _("Barcode not found")}

    def operation_has_been_canceled_elsewhere(self):
        return {
            "message_type": "warning",
            "body": _("Restart the operation, someone has canceled it."),
        }

    def no_location_found(self):
        return {
            "message_type": "error",
            "body": _("No location found for this barcode."),
        }

    def location_not_allowed(self):
        return {"message_type": "error", "body": _("Location not allowed here.")}

    def dest_location_not_allowed(self):
        return {"message_type": "error", "body": _("You cannot place it here")}

    def need_confirmation(self):
        return {"message_type": "warning", "body": _("Are you sure?")}

    def confirm_location_changed(self, from_location, to_location):
        return {
            "message_type": "warning",
            "body": _("Confirm location change from %s to %s?")
            % (from_location.name, to_location.name),
        }

    def confirm_pack_moved(self):
        return {
            "message_type": "success",
            "body": _("The pack has been moved, you can scan a new pack."),
        }

    def already_done(self):
        return {"message_type": "info", "body": _("Operation already processed.")}

    def confirm_canceled_scan_next_pack(self):
        return {
            "message_type": "success",
            "body": _("Canceled, you can scan a new pack."),
        }

    def no_pack_in_location(self, location):
        return {
            "message_type": "error",
            "body": _("Location %s doesn't contain any package." % location.name),
        }

    def several_packs_in_location(self, location):
        return {
            "message_type": "warning",
            "body": _(
                "Several packages found in %s, please scan a package." % location.name
            ),
        }

    def no_lot_for_barcode(self, barcode):
        return {
            "message_type": "error",
            "body": _("No lot found for {}".format(barcode)),
        }

    def lot_on_wrong_product(self, barcode):
        return {
            "message_type": "error",
            "body": _("Lot {} is for another product.").format(barcode),
        }

    def several_lots_in_location(self, location):
        return {
            "message_type": "warning",
            "body": _("Several lots found in %s, please scan a lot." % location.name),
        }

    def several_products_in_location(self, location):
        return {
            "message_type": "warning",
            "body": _(
                "Several products found in %s, please scan a product." % location.name
            ),
        }

    def no_pending_operation_for_pack(self, pack):
        return {
            "message_type": "error",
            "body": _("No pending operation for package %s." % pack.name),
        }

    def unrecoverable_error(self):
        return {
            "message_type": "error",
            "body": _("Unrecoverable error, please restart."),
        }

    def package_different_content(self, package):
        return {
            "message_type": "error",
            "body": _("Package {} has a different content.").format(package.name),
        }

    def x_units_put_in_package(self, qty, product, package):
        return {
            "message_type": "success",
            "body": _("{} {} put in {}").format(
                qty, product.display_name, package.name
            ),
        }

    def cannot_move_something_in_picking_type(self):
        return {
            "message_type": "error",
            "body": _("You cannot move this using this menu."),
        }

    def stock_picking_not_available(self, picking):
        return {
            "message_type": "error",
            "body": _("Transfer {} is not available.").format(picking.name),
        }

    def line_has_package_scan_package(self):
        return {
            "message_type": "warning",
            "body": _("This line has a package, please select the package instead."),
        }

    def product_multiple_packages_scan_package(self):
        return {
            "message_type": "warning",
            "body": _(
                _("This product is part of multiple packages, please scan a package.")
            ),
        }

    def product_mixed_package_scan_package(self):
        return {
            "message_type": "warning",
            "body": _(
                _(
                    "This product is part of a package with other products, "
                    "please scan a package."
                )
            ),
        }

    def product_not_found_in_pickings(self):
        return {
            "message_type": "warning",
            "body": _("No product found among current transfers."),
        }

    def lot_mixed_package_scan_package(self):
        return {
            "message_type": "warning",
            "body": _(
                _(
                    "This lot is part of a package with other products, "
                    "please scan a package."
                )
            ),
        }

    def lot_multiple_packages_scan_package(self):
        return {
            "message_type": "warning",
            "body": _("This lot is part of multiple packages, please scan a package."),
        }

    def lot_not_found_in_pickings(self):
        return {
            "message_type": "warning",
            "body": _("No lot found among current transfers."),
        }

    def batch_transfer_complete(self):
        return {
            "message_type": "success",
            "body": _("Batch Transfer complete"),
        }

    def batch_transfer_line_done(self):
        return {
            "message_type": "success",
            "body": _("Batch Transfer line done"),
        }

    def transfer_complete(self, picking):
        return {
            "message_type": "success",
            "body": _("Transfer {} complete").format(picking.name),
        }

    def location_content_transfer_item_complete(self, location_dest):
        return {
            "message_type": "success",
            "body": _("Content transfer to {} completed").format(location_dest.name),
        }

    def location_content_transfer_complete(self, location):
        return {
            "message_type": "success",
            "body": _("Location Content Transfer from {} complete").format(
                location.name
            ),
        }

    def transfer_confirm_done(self):
        return {
            "message_type": "warning",
            "body": _(
                "Not all lines have been processed, do you want to "
                "confirm partial operation ?"
            ),
        }

    def transfer_no_qty_done(self):
        return {
            "message_type": "warning",
            "body": _(
                "No quantity has been processed, unable to complete the transfer."
            ),
        }

    def recovered_previous_session(self):
        return {
            "message_type": "info",
            "body": _("Recovered previous session."),
        }

    def no_lines_to_process(self):
        return {
            "message_type": "info",
            "body": _("No lines to process."),
        }

    def location_empty(self, location):
        return {
            "message_type": "info",
            "body": _("Location {} empty").format(location.name),
        }
