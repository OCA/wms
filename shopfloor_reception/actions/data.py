# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class DataAction(Component):
    _inherit = "shopfloor.data.action"

    @property
    def _product_parser(self):
        """
        The jsonifier engine passes (record, field_name) when calling
        parser functions. We use *args to capture them.
        """
        res = super(DataAction, self)._product_parser
        return res + ["use_expiration_date"]
