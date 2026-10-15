# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component

from .utils import _replace_image_fields


class DataAction(Component):
    _inherit = "shopfloor.data.action"

    @property
    def _product_parser(self):
        res = super(DataAction, self)._product_parser
        data_detail_action = self._actions_for("data_detail")

        return _replace_image_fields(res, data_detail_action._product_image_url)
