# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _

from odoo.addons.component.core import Component


class MessageAction(Component):
    _inherit = "shopfloor.message.action"

    def location_already_inventoried(self, barcode):
        return {
            "message_type": "error",
            "body": _("This location has already been inventoried."),
        }

    def location_has_on_going_operation(self, location):
        return {
            "message_type": "error",
            "body": _(
                "This location has on-going operations. "
                "Please inventory another location and come back."
            ),
        }

    def product_or_lot_mandatory(self):
        return {"message_type": "error", "body": _("Product or lot is mandatory.")}

    def location_inventoried(self, location):
        return {
            "message_type": "success",
            "body": _("Location {0.name} successfully inventoried.").format(location),
        }

    def location_not_done(self):
        return {
            "message_type": "warning",
            "body": _(
                "Products not inventoried, are you sure you want to change location ?"
            ),
        }

    def inventory_location_not_done(self):
        return {
            "message_type": "error",
            "body": _("Not all location have been inventoried, please finalize."),
        }

    def inventory_done(self, inventory):
        return {
            "message_type": "success",
            "body": _("L'inventaire {0.name} est terminé.").format(inventory),
        }

    def inventory_already_done(self, inventory):
        return {
            "message_type": "error",
            "body": _("The inventory {0.name} is already done.").format(inventory),
        }
