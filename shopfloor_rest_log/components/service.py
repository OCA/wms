# Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.addons.component.core import AbstractComponent


class BaseRESTService(AbstractComponent):
    _inherit = "base.rest.service"

    def _log_call_in_db_values(self, _request, *args, params=None, **kw):
        values = super()._log_call_in_db_values(_request, *args, params=params, **kw)
        values.update(self._log_call_values_from_headers(values["headers"]))
        return values

    def _log_call_values_from_headers(self, headers):
        user_id = headers.get("App-User-Id", "0")
        vals = {
            "real_uid": int(user_id)
            if isinstance(user_id, str) and user_id.isdigit()
            else None,
            "app_version": headers.get("App-Version", "Unknown"),
        }
        return vals
