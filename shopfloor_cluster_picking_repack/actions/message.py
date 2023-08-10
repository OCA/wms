# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _

from odoo.addons.component.core import Component


class MessageAction(Component):
    _inherit = "shopfloor.message.action"

    def stock_picking_already_packed(self, picking):
        return {
            "message_type": "warning",
            "body": _("Transfer {} already packed.").format(picking.name),
        }

    def nbr_packages_must_be_greated_than_zero(self):
        return {
            "message_type": "error",
            "body": _("The number of packages must be greater than 0."),
        }

    def notable_to_put_in_pack(self, picking):
        return {
            "message_type": "error",
            "body": _("Not able to put in pack transfer {}.").format(picking.name),
        }

    def bin_should_be_internal(self, package):
        return {
            "message_type": "error",
            "body": _("The scanned package '{}' must be internal.").format(
                package.name
            ),
        }

    def bin_is_for_another_picking(self, package):
        return {
            "message_type": "error",
            "body": _("The scanned package '{}' is for an other picking.").format(
                package.name
            ),
        }

    def stock_picking_packed_successfully(self, picking):
        return {
            "message_type": "success",
            "body": _("Transfer {} has been packed successfully.").format(picking.name),
        }
