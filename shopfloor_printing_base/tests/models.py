# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class ShopFloorPrintingAction(Component):
    """Base Component for actions"""

    _name = "shopfloor.test.printing.action"
    _inherit = "shopfloor.printing.action"
    _collection = "shopfloor.printing"
    _usage = "test"


class ShopfloorTestFlow(Component):
    """
    Test Shopfloor Flow
    """

    _inherit = "base.shopfloor.process"
    _name = "shopfloor.test.flow"
    _collection = "shopfloor.action"
    _apply_on = "shopfloor.test.model"
    _usage = "test"
    _description = __doc__

    def test(self):
        return self._response(data={"id": id})


class ShopfloorTestValidator(Component):
    """Validators for the Test endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.test.validator"
    _usage = "test.validator"

    def test(self):
        return {"id": {"coerce": to_int, "required": True, "type": "integer"}}


class ShopfloorTestModel(models.Model):

    _name = "shopfloor.test.model"
    _description = "Test Model"
