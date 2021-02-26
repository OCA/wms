# Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.base_rest import restapi
from odoo.addons.component.core import Component


class PartnerExampleService(Component):
    """Partner example."""

    _inherit = "base.shopfloor.process"
    _name = "custom.example.partner"
    _usage = "partner_example"
    _description = __doc__

    @restapi.method(
        [(["/scan/<string:identifier>"], "GET")], auth="api_key",
    )
    def scan(self, identifier):
        """Scan a partner ref and return its data.
        """
        search = self._actions_for("search")
        record = search.partner_from_scan(identifier)
        return self._response_for_scan(record)

    @restapi.method(
        [(["/partner_list"], "GET")], auth="api_key",
    )
    def partner_list(self, **params):
        """Return list of available partners.
        """
        records = self.env["res.partner"].search([])
        return self._response_for_partner_list(records)

    @restapi.method(
        [(["/detail/<int:partner_id>"], "GET")], auth="api_key",
    )
    def detail(self, partner_id):
        """Retrieve full detail for partner ID.
        """
        record = self.env["res.partner"].browse(partner_id).exists()
        if not record:
            message = self.msg_store.generic_record_not_found()
            records = self.env["res.partner"].search([])
            return self._response_for_partner_list(records, message=message)
        return self._response_for_scan(record)

    def _response_for_scan(self, record, message=None, popup=None):
        data = {"record": self.data_detail.partner_detail(record)}
        return self._response(
            next_state="detail", data=data, message=message, popup=popup
        )

    def _response_for_partner_list(self, records, message=None, popup=None):
        data = {"records": self.data.partners(records)}
        return self._response(
            next_state="listing", data=data, message=message, popup=popup
        )


class ShopfloorCheckoutValidator(Component):

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.partner_example.validator"
    _usage = "partner_example.validator"

    def _validator_scan(self):
        return {
            "identifier": {"type": "string", "nullable": False, "required": True},
        }

    def _detail(self):
        return {
            "partner_id": {"required": True, "type": "integer"},
        }

    def _partner_list(self):
        return {}


class ShopfloorCheckoutValidatorResponse(Component):

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.partner_example.validator.response"
    _usage = "partner_example.validator.response"

    def _scan(self):
        return self._detail()

    def _detail(self):
        return self._schema.partner_detail()

    def _partner_list(self):
        return self.schema._schema_list_of(self._schema.partner())
