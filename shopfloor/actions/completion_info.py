# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _

from odoo.addons.component.core import Component


class CompletionInfo(Component):
    """Provide methods for completion info of pickings

    They are based on the module "stock_picking_completion_info" from
    OCA/stock-logistics-warehouse.
    """

    _name = "shopfloor.completion.info.action"
    _inherit = "shopfloor.process.action"
    _usage = "completion.info"

    def popup(self, move_lines):
        """Return a popup if move lines make chained pickings ready

        Return None in case no popup should be displayed.
        """
        pickings = move_lines.mapped("picking_id").filtered(
            lambda p: p.picking_type_id.display_completion_info
            and p.completion_info == "next_picking_ready"
        )
        if not pickings:
            return None
        next_pickings = pickings.mapped("move_ids.move_dest_ids.picking_id").filtered(
            lambda p: p.state == "assigned"
        )
        if not next_pickings:
            return None
        return {
            "body": _(
                "Last operation of transfer %(picking_names)s. "
                "Next operation (%(next_picking_names)s) is ready to proceed.",
                picking_names=", ".join(pickings.mapped("name")),
                next_picking_names=", ".join(next_pickings.mapped("name")),
            )
        }
