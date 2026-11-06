# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class DataAction(Component):
    _inherit = "shopfloor.data.action"

    @property
    def _product_parser(self):
        res = super(DataAction, self)._product_parser
        return res + ["immediately_usable_qty"]
