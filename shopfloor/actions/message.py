# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import _

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class MessageAction(Component):
    _inherit = "shopfloor.message.action"

    def no_operation_found(self):
        return {
            "message_type": "error",
            "body": _("No operation found for this menu and profile."),
        }

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

    def package_has_no_product_to_take(self, barcode):
        return {
            "message_type": "error",
            "body": _("The package %s doesn't contain any product to take.") % barcode,
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

    def location_requires_package(self):
        return {
            "message_type": "warning",
            "body": _(
                "This location requires packages. Please scan a destination package."
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
            "body": _("This transfer does not exist or is not available anymore."),
        }

    def package_not_found(self):
        return {
            "message_type": "error",
            "body": _("This package does not exist anymore."),
        }

    def package_different_change(self):
        return {
            "message_type": "warning",
            "body": _(
                "You scanned a different package with the same product, "
                "do you want to change pack? Scan it again to confirm"
            ),
        }

    def package_not_available_in_picking(self, package, picking):
        return {
            "message_type": "warning",
            "body": _("Package {} is not available in transfer {}.").format(
                package.name, picking.name
            ),
        }

    def package_not_empty(self, package):
        return {
            "message_type": "warning",
            "body": _("Package {} is not empty.").format(package.name),
        }

    def package_already_used(self, package):
        return {
            "message_type": "warning",
            "body": _("Package {} is already used.").format(package.name),
        }

    def package_different_picking_type(self, package, picking_type):
        return {
            "message_type": "warning",
            "body": _(
                "Package {} contains already lines from a different operation type {}"
            ).format(package.name, picking_type.name),
        }

    def dest_package_required(self):
        return {
            "message_type": "warning",
            "body": _("A destination package is required."),
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

    def move_already_done(self):
        return {"message_type": "warning", "body": _("Move already processed.")}

    def confirm_canceled_scan_next_pack(self):
        return {
            "message_type": "success",
            "body": _("Canceled, you can scan a new pack."),
        }

    def no_pack_in_location(self, location):
        return {
            "message_type": "error",
            "body": _("Location %s doesn't contain any package.") % location.name,
        }

    def several_packs_in_location(self, location):
        return {
            "message_type": "warning",
            "body": _(
                "Several packages found in %s, please scan a package." % location.name
            ),
        }

    def no_package_or_lot_for_barcode(self, barcode):
        return {
            "message_type": "error",
            "body": _("No package or lot found for barcode {}.").format(barcode),
        }

    def no_product_for_barcode(self, barcode):
        return {
            "message_type": "error",
            "body": _("No product found for {}").format(barcode),
        }

    def wrong_product(self):
        # Method to drop in v15
        _logger.warning("`wrong_product` is deprecated, use `wrong_record` instead")
        return {
            "message_type": "error",
            "body": self._wrong_record_msg("product.product"),
        }

    def _wrong_record_msg(self, model_name):
        return {
            "product.product": _("Wrong product."),
            "stock.production.lot": _("Wrong lot."),
            "stock.location": _("Wrong location."),
            "stock.quant.package": _("Wrong pack."),
            "product.packaging": _("Wrong packaging."),
        }.get(model_name, _("Wrong."))

    def wrong_record(self, record):
        return {"message_type": "error", "body": self._wrong_record_msg(record._name)}

    def no_lot_for_barcode(self, barcode):
        return {
            "message_type": "error",
            "body": _("No lot found for {}").format(barcode),
        }

    def lot_on_wrong_product(self, barcode):
        return {
            "message_type": "error",
            "body": _("Lot {} is for another product.").format(barcode),
        }

    def wrong_lot(self):
        # Method to drop in v15
        _logger.warning("`wrong_log` is deprecated, use `wrong_record` instead")
        return {
            "message_type": "error",
            "body": self._wrong_record_msg("stock.production.lot"),
        }

    def several_lots_in_location(self, location):
        return {
            "message_type": "warning",
            "body": _("Several lots found in %s, please scan a lot.") % location.name,
        }

    def several_lots_in_package(self, package):
        return {
            "message_type": "error",
            "body": _("Several lots found in %s, please scan the lot." % package.name),
        }

    def several_move_in_different_location(self):
        return {
            "message_type": "warning",
            "body": _(
                "Several moves found on different locations, please scan first the location."
            ),
        }

    def several_move_with_different_lot(self):
        return {
            "message_type": "warning",
            "body": _("Several moves found for different lots, please scan the lot."),
        }

    def several_products_in_location(self, location):
        return {
            "message_type": "warning",
            "body": _(
                "Several products found in %s, please scan a product." % location.name
            ),
        }

    def several_products_in_package(self, package):
        return {
            "message_type": "error",
            "body": _(
                "Several products found in %s, please scan the product." % package.name
            ),
        }

    def no_product_in_location(self, location):
        return {
            "message_type": "error",
            "body": _("No product found in {}").format(location.name),
        }

    def no_pending_operation_for_pack(self, pack):
        return {
            "message_type": "error",
            "body": _("No pending operation for package %s.") % pack.name,
        }

    def no_putaway_destination_available(self):
        return {
            "message_type": "error",
            "body": _("No putaway destination is available."),
        }

    def package_unable_to_transfer(self, pack):
        return {
            "message_type": "error",
            "body": _("The package %s cannot be transferred with this scenario.")
            % pack.name,
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

    def package_change_error_same_package(self, package):
        return {
            "message_type": "error",
            "body": _("Same package {} is already assigned.").format(package.name),
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

    def scan_the_location_first(self):
        return {
            "message_type": "warning",
            "body": _("Please scan the location first."),
        }

    def scan_the_package(self):
        return {
            "message_type": "warning",
            "body": _("Please scan the package."),
        }

    def product_multiple_packages_scan_package(self):
        return {
            "message_type": "warning",
            "body": _(
                _("This product is part of multiple packages, please scan a package.")
            ),
        }

    def source_document_multiple_pickings_scan_package(self):
        return {
            "message_type": "warning",
            "body": _(
                _(
                    "This source document is part of multiple transfers, please scan a package."
                )
            ),
        }

    def product_mixed_package_scan_package(self):
        return {
            "message_type": "warning",
            "body": _(
                "This product is part of a package with other products, "
                "please scan a package."
            ),
        }

    def product_not_unitary_in_package_scan_package(self):
        return {
            "message_type": "warning",
            "body": _("This product is part of a package, please scan a package."),
        }

    def product_not_found(self):
        return {
            "message_type": "error",
            "body": _("This product does not exist anymore."),
        }

    def product_not_found_in_pickings(self):
        return {
            "message_type": "warning",
            "body": _("No transfer found for this product."),
        }

    def product_not_found_in_location_or_transfer(self, product, location, picking):
        return {
            "message_type": "error",
            "body": _(
                "Product {} not found in location {} or transfer {}.".format(
                    product.name, location.name, picking.name
                )
            ),
        }

    def x_not_found_or_already_in_dest_package(self, message_code):
        return {
            "message_type": "warning",
            "body": _(
                "{} not found in the current transfer or already in a package.".format(
                    message_code
                )
            ),
        }

    def packaging_not_found_in_picking(self):
        return {
            "message_type": "warning",
            "body": _("Packaging not found in the current transfer."),
        }

    def packaging_dimension_updated(self, packaging):
        return {
            "message_type": "success",
            "body": _("Packaging {} dimension updated.").format(packaging.name),
        }

    def expiration_date_missing(self):
        return {
            "message_type": "error",
            "body": _("Missing expiration date."),
        }

    def multiple_picks_found_select_manually(self):
        return {
            "message_type": "error",
            "body": _("Several transfers found, please select a transfer manually."),
        }

    def no_transfer_for_packaging(self):
        return {
            "message_type": "error",
            "body": _("No transfer found for the scanned packaging."),
        }

    def no_transfer_for_lot(self):
        return {
            "message_type": "error",
            "body": _("No transfer found for the scanned lot."),
        }

    def create_new_pack_ask_confirmation(self, barcode):
        return {
            "message_type": "warning",
            "body": _("Create new PACK {}? Scan it again to confirm.").format(barcode),
        }

    def place_in_location_ask_confirmation(self, location_name):
        return {
            "message_type": "warning",
            "body": _("Place it in {}?").format(location_name),
        }

    def product_not_found_in_current_picking(self):
        return {
            "message_type": "error",
            "body": _("Product is not in the current transfer."),
        }

    def lot_mixed_package_scan_package(self):
        return {
            "message_type": "warning",
            "body": _(
                "This lot is part of a package with other products, "
                "please scan a package."
            ),
        }

    def lot_multiple_packages_scan_package(self):
        return {
            "message_type": "warning",
            "body": _("This lot is part of multiple packages, please scan a package."),
        }

    def lot_not_found(self):
        return {
            "message_type": "error",
            "body": _("This lot does not exist anymore."),
        }

    def lot_not_found_in_pickings(self):
        return {
            "message_type": "warning",
            "body": _("No transfer found for this lot."),
        }

    def lot_not_found_in_location(self, lot, location):
        return {
            "message_type": "error",
            "body": _("Lot {} not found in location {}").format(
                lot.name, location.name
            ),
        }

    def lot_not_found_in_picking(self, lot, picking):
        return {
            "message_type": "error",
            "body": _("Lot {} not found in transfer {}").format(lot.name, picking.name),
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

    def location_content_transfer_complete(self, location_src, location_dest):
        return {
            "message_type": "success",
            "body": _("Content transferred from {} to {}.").format(
                location_src.name, location_dest.name
            ),
        }

    def location_content_unable_to_transfer(self, location_dest):
        return {
            "message_type": "error",
            "body": _(
                "The content of {} cannot be transferred with this scenario."
            ).format(location_dest.name),
        }

    def product_in_multiple_sublocation(self, product):
        return {
            "message_type": "warning",
            "body": _(
                "Product {} found in multiple locations. Scan your location first."
            ).format(product.name),
        }

    def lot_in_multiple_sublocation(self, lot):
        return {
            "message_type": "warning",
            "body": _(
                "Lot {lot} for product {product} found in multiple locations. "
                "Scan your location first."
            ).format(lot=lot.name, product=lot.product_id.name),
        }

    def no_default_location_on_picking_type(self):
        return {
            "message_type": "error",
            "body": _(
                "Operation types for this menu are missing "
                "default source and destination locations."
            ),
        }

    def location_src_set_to_sublocation(self, location_src):
        return {
            "message_type": "success",
            "body": _("Working location changed to {}").format(location_src.name),
        }

    def picking_already_started_in_location(self, pickings):
        return {
            "message_type": "error",
            "body": _(
                "Picking has already been started in this location in transfer(s): {}"
            ).format(", ".join(pickings.mapped("name"))),
        }

    def transfer_done_success(self, picking):
        return {
            "message_type": "success",
            "body": _("Transfer {} done").format(picking.name),
        }

    def transfer_confirm_done(self):
        return {
            "message_type": "warning",
            "body": _(
                "Not all lines have been processed with full quantity. "
                "Do you confirm partial operation?"
            ),
        }

    def move_already_returned(self):
        return {
            "message_type": "error",
            "body": _("The product/packaging you selected has already been returned."),
        }

    def return_line_invalid_qty(self):
        return {
            "message_type": "error",
            "body": _("You cannot return more quantity than what was initially sent."),
        }

    def transfer_no_qty_done(self):
        return {
            "message_type": "warning",
            "body": _(
                "No quantity has been processed, unable to complete the transfer."
            ),
        }

    def picking_zero_quantity(self):
        return {
            "message_type": "error",
            "body": _("The picked quantity must be a value above zero."),
        }

    def selected_lines_qty_done_higher_than_allowed(self):
        return {
            "message_type": "warning",
            "body": _(
                "The quantity scanned for one or more lines cannot be "
                "higher than the maximum allowed."
            ),
        }

    def line_scanned_qty_done_higher_than_allowed(self):
        return {
            "message_type": "warning",
            "body": _(
                "Please note that the scanned quantity is higher than the maximum allowed."
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

    def no_lines_to_process_set_quantities(self):
        return {
            "message_type": "info",
            "body": _("No lines to process, set quantities on some"),
        }

    def location_empty(self, location):
        return {
            "message_type": "error",
            "body": _("Location {} empty").format(location.name),
        }

    def location_empty_scan_package(self, location):
        return {
            "message_type": "warning",
            "body": _("Location empty. Try scanning a package"),
        }

    def location_not_found(self):
        return {
            "message_type": "error",
            "body": _("This location does not exist."),
        }

    def unable_to_pick_more(self, quantity):
        return {
            "message_type": "error",
            "body": _("You must not pick more than {} units.").format(quantity),
        }

    def unable_to_pick_qty(self):
        return {
            "message_type": "error",
            "body": _("You cannot process that much units."),
        }

    def lot_replaced_by_lot(self, old_lot, new_lot):
        return {
            "message_type": "success",
            "body": _("Lot {} replaced by lot {}.").format(old_lot.name, new_lot.name),
        }

    def package_replaced_by_package(self, old_package, new_package):
        return {
            "message_type": "success",
            "body": _("Package {} replaced by package {}.").format(
                old_package.name, new_package.name
            ),
        }

    def package_already_picked_by(self, package, picking):
        return {
            "message_type": "error",
            "body": _(
                "Package {} cannot be picked, already moved by transfer {}."
            ).format(package.name, picking.name),
        }

    def units_replaced_by_package(self, new_package):
        return {
            "message_type": "success",
            "body": _("Units replaced by package {}.").format(new_package.name),
        }

    def package_change_error(self, package, error_msg):
        return {
            "message_type": "error",
            "body": _("Package {} cannot be used: {} ").format(package.name, error_msg),
        }

    def package_not_found_in_location(self, package, location):
        return {
            "message_type": "error",
            "body": _("Package {} not found in location {}").format(
                package.name, location.name
            ),
        }

    def package_not_found_in_picking(self, package, picking):
        return {
            "message_type": "error",
            "body": _("Package {} not found in transfer {}").format(
                package.name, picking.name
            ),
        }

    def cannot_change_lot_already_picked(self, lot):
        return {
            "message_type": "error",
            "body": _("Cannot change to lot {} which is entirely picked.").format(
                lot.name
            ),
        }

    def buffer_complete(self):
        return {
            "message_type": "success",
            "body": _("All packages processed."),
        }

    def picking_type_complete(self, picking_type):
        return {
            "message_type": "success",
            "body": _("Picking type {} complete.").format(picking_type.name),
        }

    def barcode_no_match(self, barcode):
        return {
            "message_type": "warning",
            "body": _("Barcode does not match with {}.").format(barcode),
        }

    def lines_different_dest_location(self):
        return {
            "message_type": "error",
            "body": _("Lines have different destination location."),
        }

    def new_move_lines_not_assigned(self):
        return {
            "message_type": "error",
            "body": _("New move lines cannot be assigned: canceled."),
        }

    def package_open(self):
        return {
            "message_type": "info",
            "body": _("Package has been opened. You can move partial quantities."),
        }

    def packaging_invalid_for_carrier(self, packaging, carrier):
        return {
            "message_type": "error",
            "body": _("Packaging '{}' is not allowed for carrier {}.").format(
                packaging.name if packaging else _("No value"), carrier.name
            ),
        }

    def dest_package_not_valid(self, package):
        return {
            "message_type": "error",
            "body": _("{} is not a valid destination package.").format(package.name),
        }

    def no_valid_package_to_select(self):
        return {
            "message_type": "warning",
            "body": _("No valid package to select."),
        }

    def no_delivery_packaging_available(self):
        return {
            "message_type": "warning",
            "body": _("No delivery package type available."),
        }

    def goods_packed_in(self, package):
        return {
            "message_type": "info",
            "body": _("Goods packed into {0.name}").format(package),
        }

    def picking_without_carrier_cannot_pack(self, picking):
        return {
            "message_type": "error",
            "body": _(
                "Pick + Pack mode ON: the picking {0.name} has no carrier set. "
                "The system couldn't pack goods automatically."
            ).format(picking),
        }

    def no_work_found(self):
        return {
            "message_type": "warning",
            "body": _("No available work could be found."),
        }

    def confirm_put_all_goods_in_delivery_package(self, packaging_type):
        return {
            "message_type": "warning",
            "body": _(
                "Delivery package type scanned: %(name)s. "
                "Scan again to place all goods in the same package."
            )
            % dict(name=packaging_type.name),
        }

    def location_contains_only_packages_scan_one(self):
        return {
            "message_type": "warning",
            "body": _("This location only contains packages, please scan one of them."),
        }

    def no_line_to_pack(self):
        return {
            "message_type": "warning",
            "body": _("No line to pack found."),
        }

    def package_transfer_not_allowed_scan_location(self):
        return {
            "message_type": "warning",
            "body": _(
                "Transferring to a different package is not allowed, "
                "please scan a location instead."
            ),
        }
