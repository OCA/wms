# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class DataAction(Component):

    _inherit = "shopfloor.data.action"

    def move_line(self, record, with_picking=False, **kw):
        """
        We add here a string list of locations suggestions
        Note: the presence of locations here depends on
        picking type configuration (see: stock_picking_operation_destination_suggest).
        """
        data = super().move_line(record, with_picking, **kw)
        if data:
            data.update(
                {
                    "location_destination_suggestions": ", ".join(
                        location.name
                        for location in record.picking_id.destination_location_suggestion_ids
                    )
                }
            )
        return data
