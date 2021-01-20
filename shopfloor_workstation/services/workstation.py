# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class ShopfloorWorkstation(Component):
    """
    Workstation service for the mobile application.

    This allows to scan a workstation bar code on the floor, which
    will set a default profile on the mobile app and offer the option
    to change some configuration of the connected user.

    """

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.workstation"
    _usage = "workstation"
    _description = __doc__

    def setdefault(self, barcode):
        """Endpoint that receives a scanned barcode."""
        ws = self.env["shopfloor.workstation"].search([("barcode", "=", barcode)])
        if ws:
            ws.set_as_default_on_user(self.env.user)
            message = {
                "message_type": "info",
                "body": _("Default workstation set to {}").format(ws.name),
            }
        else:
            message = {
                "message_type": "error",
                "body": _("Workstation not found"),
            }
        return self._response(
            message=message, data=self._convert_one_record(ws) if ws else {},
        )

    def _convert_one_record(self, record):
        profile_data = None
        if record.shopfloor_profile_id:
            profile_data = {
                "id": record.shopfloor_profile_id.id,
                "name": record.shopfloor_profile_id.name,
            }
        return {
            "id": record.id,
            "name": record.name,
            "barcode": record.barcode,
            "profile": profile_data,
        }


class ShopfloorWorkstationValidator(Component):
    """Validators for the Workstation endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.workstation.validator"
    _usage = "workstation.validator"

    def setdefault(self):
        return {"barcode": {"type": "string", "nullable": True, "required": False}}


class ShopfloorWorkstationValidatorResponse(Component):
    """Validators for the Workstation endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.workstation.validator.response"
    _usage = "workstation.validator.response"

    def setdefault(self):
        return self._response_schema(self._record_schema)

    @property
    def _record_schema(self):
        return {
            "id": {"coerce": to_int, "required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "barcode": {"type": "string", "nullable": False, "required": True},
            "profile": {
                "type": "dict",
                "nullable": True,
                "schema": {
                    "id": {"coerce": to_int, "required": True, "type": "integer"},
                    "name": {"type": "string", "nullable": False, "required": True},
                },
            },
        }
