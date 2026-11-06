# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2020 Akretion (http://www.akretion.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.addons.component.core import AbstractComponent


class BaseShopfloorService(AbstractComponent):
    """Base class for REST services"""

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

    def _response(
        self, base_response=None, data=None, next_state=None, message=None, popup=None
    ):
        if self._menu.display_print_label_button:
            data = data or {}
            data["allow_print_label"] = True

        return super()._response(
            base_response=base_response,
            data=data,
            next_state=next_state,
            message=message,
            popup=popup,
        )
