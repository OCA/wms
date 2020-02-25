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
            "message": _("No operation type found for this menu and profile."),
        }

    def several_picking_types(self):
        return {
            "message_type": "error",
            "message": _("Several operation types found for this menu and profile."),
        }

    def package_not_found_for_barcode(self, barcode):
        return {
            "message_type": "error",
            "message": _("The package %s doesn't exist") % barcode,
        }

    def package_not_allowed_in_src_location(self, barcode, picking_type):
        return {
            "message_type": "error",
            "message": _("You cannot work on a package (%s) outside of location: %s")
            % (barcode, picking_type.default_location_src_id.name),
        }

    def already_running_ask_confirmation(self):
        return {
            "message_type": "warning",
            "message": _(
                "Operation's already running. Would you like to take it over?"
            ),
        }

    def scan_destination(self):
        return {"message_type": "info", "message": _("Scan the destination location")}

    def scan_lot_on_product_tracked_by_lot(self):
        return {
            "message_type": "warning",
            "message": _("Product tracked by lot, please scan one."),
        }

    def operation_not_found(self):
        return {
            "message_type": "error",
            "message": _("This operation does not exist anymore."),
        }

    def record_not_found(self):
        return {
            "message_type": "error",
            "message": _("This record you were working on does not exist anymore."),
        }

    def barcode_not_found(self):
        return {"message_type": "error", "message": _("Barcode not found")}

    def operation_has_been_canceled_elsewhere(self):
        return {
            "message_type": "warning",
            "message": _("Restart the operation, someone has canceled it."),
        }

    def no_location_found(self):
        return {
            "message_type": "error",
            "message": _("No location found for this barcode."),
        }

    def dest_location_not_allowed(self):
        return {"message_type": "error", "message": _("You cannot place it here")}

    def need_confirmation(self):
        return {"message_type": "warning", "message": _("Are you sure?")}

    def confirm_location_changed(self, from_location, to_location):
        return {
            "message_type": "warning",
            "message": _("Confirm location change from %s to %s?")
            % (from_location.name, to_location.name),
        }

    def confirm_pack_moved(self):
        return {
            "message_type": "success",
            "message": _("The pack has been moved, you can scan a new pack."),
        }

    def already_done(self):
        return {"message_type": "info", "message": _("Operation already processed.")}

    def confirm_canceled_scan_next_pack(self):
        return {
            "message_type": "info",
            "message": _("Canceled, you can scan a new pack."),
        }

    def no_pack_in_location(self, location):
        return {
            "message_type": "error",
            "message": _("Location %s doesn't contain any package." % location.name),
        }

    def several_packs_in_location(self, location):
        return {
            "message_type": "warning",
            "message": _(
                "Several packages found in %s, please scan a package." % location.name
            ),
        }

    def several_lots_in_location(self, location):
        return {
            "message_type": "warning",
            "message": _(
                "Several lots found in %s, please scan a lot." % location.name
            ),
        }

    def several_products_in_location(self, location):
        return {
            "message_type": "warning",
            "message": _(
                "Several products found in %s, please scan a product." % location.name
            ),
        }

    def no_pending_operation_for_pack(self, pack):
        return {
            "message_type": "error",
            "message": _("No pending operation for package %s." % pack.name),
        }
