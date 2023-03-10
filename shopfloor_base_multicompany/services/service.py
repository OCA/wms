# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo import _, exceptions

from odoo.addons.component.core import AbstractComponent


class BaseShopfloorService(AbstractComponent):

    _inherit = "base.shopfloor.service"

    def dispatch(self, method_name, *args, params=None):
        self._validate_company()
        return super().dispatch(method_name, *args, params=params)

    def _validate_company(self):
        """
        Validate current user's companies match one of the companies allowed for the app.

        Raises:
        exceptions.UserError: If the user's company is not allowed.
        """
        if self.collection.must_validate_company:
            if self.env.user.company_id.id not in self.collection.company_ids.ids:
                raise exceptions.UserError(self._validate_company_error_msg())

    def _validate_company_error_msg(self):
        return _("Current user belongs to a company that is not allowed on this app.")
