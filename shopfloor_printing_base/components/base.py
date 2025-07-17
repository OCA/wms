# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.component.components.base import AbstractComponent


class ShopFloorProcessAction(AbstractComponent):
    """Base Component for actions"""

    _inherit = "base.shopfloor.service"

    def _printing_for(self, usage):
        """
        Return the good printing component for
        the current usage.
        """
        printings = self.work.components_registry.lookup(
            collection_name="shopfloor.printing", usage=usage
        )
        return printings[0](self.work)
