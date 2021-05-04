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
        [(["/scan/<string:identifier>"], "GET")],
        output_param=restapi.CerberusValidator("scan"),
        auth="api_key",
    )
    def scan(self, identifier):
        """Scan a partner ref and return its data.
        """
        search = self._actions_for("search")
        record = search.partner_from_scan(identifier)
        return self._response_for_scan(record)

    @restapi.method(
        [(["/partner_list"], "GET")],
        input_param=restapi.CerberusValidator("partner_list"),
        output_param=restapi.CerberusValidator("partner_list"),
        auth="api_key",
    )
    def partner_list(self, **params):
        """Return list of available partners.
        """
        domain = []
        if "name" in params:
            domain.append(("name", "like", params["name"]))
        records = self.env["res.partner"].search(domain)
        return self._response_for_partner_list(records)

    @restapi.method(
        [(["/detail/<int:partner_id>"], "GET")],
        output_param=restapi.CerberusValidator("detail"),
        auth="api_key",
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

    def partner_list(self):
        return {
            "name": {"required": False, "type": "string"},
        }


class ShopfloorCheckoutValidatorResponse(Component):

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.partner_example.validator.response"
    _usage = "partner_example.validator.response"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {
            "start": {},
            "detail": {
                "record": self.schemas._schema_dict_of(
                    self.schemas_detail.partner_detail()
                )
            },
            "listing": {
                "records": self.schemas._schema_list_of(self.schemas.partner()),
            },
        }

    def scan(self):
        return self.detail()

    def detail(self):
        return self._response_schema(next_states=["detail"])

    def partner_list(self):
        return self._response_schema(next_states=["listing"])
