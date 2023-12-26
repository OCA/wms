# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo import _

from odoo.addons.component.core import AbstractComponent, Component

from ..actions.base_action import get_actions_for


class ShopfloorScanAnything(Component):
    """Endpoints to scan any record.

    You can register your own record scanner.

    NOTE for swagger docs: using `anyof_schema` for `record` response key
    does not work in swagger UI. Hence, you won't see any detail.

    Issue: https://github.com/swagger-api/swagger-ui/issues/3803
    PR: https://github.com/swagger-api/swagger-ui/pull/5530
    """

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.scan.anything"
    _usage = "scan_anything"
    _description = __doc__

    def scan(self, identifier, record_types=None):
        """Scan an item identifier and return its info if found.

        :param identifier: a string, normally a barcode or name
        :param record_types: limit scan to specific record types
        """
        data = {}
        tried = []
        record = None
        for handler in self._scan_handlers():
            if record_types and handler.record_type not in record_types:
                continue
            tried.append(handler.record_type)
            record = handler.search(identifier)
            if record:
                data.update(
                    {
                        "identifier": identifier,
                        "record": handler.converter(record),
                        "type": handler.record_type,
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
        """Return components to handle scan requests."""
        return self.many_components(usage="scan_anything.handler")


class ShopfloorScanAnythingHandler(AbstractComponent):
    """Handle record search for ScanAnything service."""

    _name = "shopfloor.scan.anything.handler"
    _usage = "scan_anything.handler"
    _description = __doc__
    _collection = "shopfloor.app"
    _actions_collection_name = "shopfloor.action"

    @property
    def _data(self):
        return get_actions_for(self, "data")

    @property
    def _data_detail(self):
        return get_actions_for(self, "data_detail")

    @property
    def _schema(self):
        return get_actions_for(self, "schema")

    @property
    def _schema_detail(self):
        return get_actions_for(self, "schema_detail")

    @property
    def _search(self):
        return get_actions_for(self, "search")

    @property
    def record_type(self):
        """Return unique record type for this handler"""
        raise NotImplementedError()

    def search(self, identifier):
        """Find and return Odoo record."""
        raise NotImplementedError()

    @property
    def converter(self):
        """Return data converter to json."""
        raise NotImplementedError()

    @property
    def schema(self):
        """Return schema to validate record converter."""
        raise NotImplementedError()


class ShopfloorScanAnythingValidator(Component):
    """Validators for the Application endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.scan_anything.validator"
    _usage = "scan_anything.validator"

    def scan(self):
        return {
            "identifier": {"type": "string", "nullable": False, "required": True},
            "record_types": {"type": "list", "nullable": True, "required": False},
        }


class ShopfloorScanAnythingValidatorResponse(Component):
    """Validators for the scan anything endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.scan_anything.validator.response"
    _usage = "scan_anything.validator.response"

    def scan(self):
        scan_service = self.component(usage="scan_anything")
        allowed_types = [x.record_type for x in scan_service._scan_handlers()]
        allowed_schemas = [x.schema() for x in scan_service._scan_handlers()]
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
