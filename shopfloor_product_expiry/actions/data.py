# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component


class DataAction(Component):
    _inherit = "shopfloor.data.action"

    @property
    def _move_line_parser(self):
        # This will add expiration date filled in on move lines
        data = super()._move_line_parser
        data.append("expiration_date")
        return data
