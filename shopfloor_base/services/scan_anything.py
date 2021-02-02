# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _

from odoo.addons.component.core import Component


class ShopfloorScanAnything(Component):
    """Endpoints to scan any record.

    Supported types of records (models):

    * location (stock.location)
    * package (stock.quant.package)
    * product (product.product)
    * lot (stock.production.lot)
    * transfer (stock.picking)

    NOTE for swagger docs: using `anyof_schema` for `record` response key
    does not work in swagger UI. Hence, you won't see any detail.

    Issue: https://github.com/swagger-api/swagger-ui/issues/3803
    PR: https://github.com/swagger-api/swagger-ui/pull/5530
    """

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.scan.anything"
    _usage = "scan_anything"
    _description = __doc__

    def scan(self, identifier):
        # TODO: shall we add constrains by profile etc?
        data = {}
        tried = []
        record = None
        for rec_type, finder, converter, __ in self._scan_handlers():
            tried.append(rec_type)
            record = finder(identifier)
            if record:
                data.update(
                    {
                        "identifier": identifier,
                        "record": converter(record),
                        "type": rec_type,
                    }
                )
                break
        if not record:
            return self._response_for_not_found(tried)
        return self._response_for_found(data)

    def _response_for_found(self, data):
        return self._response(data=data)

    def _response_for_not_found(self, tried):
        message = {
            "body": _(
                "Record not found.\n" "We've tried with the following types: {}"
            ).format(", ".join(tried)),
            "message_type": "error",
        }
        return self._response(message=message)

    def _scan_handlers(self):
        """Return a tuple of tuples describing handlers for scan requests.

        Tuple schema:

            0. record type
            1. finder
            2. json detail converter
            3. detail schema validator

        """
        search = self.actions_for("search")
        schema = self.component(usage="schema_detail")
        return (
            (
                "location",
                search.location_from_scan,
                self.data_detail.location_detail,
                schema.location_detail,
            ),
            (
                "package",
                search.package_from_scan,
                self.data_detail.package_detail,
                schema.package_detail,
            ),
            (
                "product",
                search.product_from_scan,
                self.data_detail.product_detail,
                schema.product_detail,
            ),
            (
                "lot",
                search.lot_from_scan,
                self.data_detail.lot_detail,
                schema.lot_detail,
            ),
            (
                "transfer",
                search.picking_from_scan,
                self.data_detail.picking_detail,
                schema.picking_detail,
            ),
        )


class ShopfloorScanAnythingValidator(Component):
    """Validators for the Application endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.scan_anything.validator"
    _usage = "scan_anything.validator"

    def scan(self):
        return {
            "identifier": {"type": "string", "nullable": False, "required": True},
        }


class ShopfloorScanAnythingValidatorResponse(Component):
    """Validators for the scan anything endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.scan_anything.validator.response"
    _usage = "scan_anything.validator.response"

    def scan(self):
        scan_service = self.component(usage="scan_anything")
        allowed_types = [x[0] for x in scan_service._scan_handlers()]
        allowed_schemas = [x[-1]() for x in scan_service._scan_handlers()]
        data_schema = {
            "identifier": {"type": "string", "nullable": True, "required": False},
            "type": {
                "type": "string",
                "nullable": True,
                "required": False,
                "allowed": allowed_types,
            },
            "record": {
                "type": "dict",
                "required": False,
                "nullable": True,
                "anyof_schema": allowed_schemas,
                "dependencies": ["identifier", "type"],
            },
        }
        return self._response_schema(data_schema)
