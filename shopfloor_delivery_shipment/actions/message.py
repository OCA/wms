# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import _

from odoo.addons.component.core import Component


class MessageAction(Component):
    _inherit = "shopfloor.message.action"

    def no_shipment_in_progress(self):
        return {
            "message_type": "error",
            "body": _("No shipment advice in progress found for this loading dock."),
        }

    def scan_dock_again_to_confirm(self, dock):
        return {
            "message_type": "error",
            "body": _(
                "No shipment advice in progress found for this loading dock. "
                "Scan again {} to create a new one."
            ).format(dock.name),
        }

    def picking_not_planned_in_shipment(self, picking, shipment_advice):
        return {
            "message_type": "error",
            "body": _("Transfer {} has not been planned in the shipment {}.").format(
                picking.name,
                shipment_advice.name,
            ),
        }

    def package_not_planned_in_shipment(self, package, shipment_advice):
        return {
            "message_type": "error",
            "body": _("Package {} has not been planned in the shipment {}.").format(
                package.name,
                shipment_advice.name,
            ),
        }

    def lot_not_planned_in_shipment(self, lot, shipment_advice):
        return {
            "message_type": "error",
            "body": _("Lot {} has not been planned in the shipment {}.").format(
                lot.name,
                shipment_advice.name,
            ),
        }

    def product_not_planned_in_shipment(self, product, shipment_advice):
        return {
            "message_type": "error",
            "body": _("Product {} has not been planned in the shipment {}.").format(
                product.barcode,
                shipment_advice.name,
            ),
        }

    def unable_to_load_package_in_shipment(self, package, shipment_advice):
        return {
            "message_type": "error",
            "body": _("Package {} can not been loaded in the shipment {}.").format(
                package.name,
                shipment_advice.name,
            ),
        }

    def unable_to_load_lot_in_shipment(self, lot, shipment_advice):
        return {
            "message_type": "error",
            "body": _("Lot {} can not been loaded in the shipment {}.").format(
                lot.name,
                shipment_advice.name,
            ),
        }

    def unable_to_load_product_in_shipment(self, product, shipment_advice):
        return {
            "message_type": "error",
            "body": _("Product {} can not been loaded in the shipment {}.").format(
                product.barcode,
                shipment_advice.name,
            ),
        }

    def package_already_loaded_in_shipment(self, package, shipment_advice):
        return {
            "message_type": "warning",
            "body": _("Package {} is already loaded in the shipment {}.").format(
                package.name,
                shipment_advice.name,
            ),
        }

    def lot_already_loaded_in_shipment(self, lot, shipment_advice):
        return {
            "message_type": "warning",
            "body": _("Lot {} is already loaded in the shipment {}.").format(
                lot.name,
                shipment_advice.name,
            ),
        }

    def product_already_loaded_in_shipment(self, product, shipment_advice):
        return {
            "message_type": "warning",
            "body": _("Product {} is already loaded in the shipment {}.").format(
                product.name,
                shipment_advice.name,
            ),
        }

    def carrier_not_allowed_by_shipment(self, picking):
        return {
            "message_type": "error",
            "body": _(
                "Delivery method {} not permitted for this shipment advice."
            ).format(picking.carrier_id.name),
        }

    def no_delivery_content_to_load(self, picking):
        return {
            "message_type": "error",
            "body": _("No more content to load from delivery {}.").format(picking.name),
        }

    def scan_operation_first(self):
        return {
            "message_type": "error",
            "body": _("Please first scan the operation."),
        }

    def product_owned_by_packages(self, packages):
        return {
            "message_type": "error",
            "body": _("Please scan package(s) {} where this product is.").format(
                ", ".join(packages.mapped("name"))
            ),
        }

    def product_owned_by_lots(self, lots):
        return {
            "message_type": "error",
            "body": _("Please scan lot(s) {} where this product is.").format(
                ", ".join(lots.mapped("name"))
            ),
        }

    def lot_owned_by_packages(self, packages):
        return {
            "message_type": "error",
            "body": _("Please scan package(s) {} where this lot is.").format(
                ", ".join(packages.mapped("name"))
            ),
        }

    def shipment_planned_content_fully_loaded(self):
        return {
            "message_type": "info",
            "body": _("Planned content has been fully loaded."),
        }

    def shipment_validated(self, shipment_advice):
        return {
            "message_type": "info",
            "body": _("Shipment {} is validated.").format(shipment_advice.name),
        }
