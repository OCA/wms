# Copyright 2026 ACSONE SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component
from odoo.addons.shopfloor_base.utils import ensure_model


class DataAction(Component):
    _inherit = "shopfloor.data.action"

    @ensure_model("product.packaging.level")
    def packaging_level(self, record, **kw):
        return self._jsonify(record, self._simple_record_parser(), **kw)

    def packaging_levels(self, record, **kw):
        return self.packaging_level(record, multi=True)
