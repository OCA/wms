# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.addons.component.core import Component

from .common import CommonCase
from .common_misc import ScanAnythingTestMixin


class ScanAnythingCase(CommonCase, ScanAnythingTestMixin):
    def _get_test_handlers(self):
        class PartnerFinder(Component):
            _name = "shopfloor.scan.partner.handler"
            _inherit = "shopfloor.scan.anything.handler"

            record_type = "testpartner"

            def search(self, identifier):
                return (
                    self.env["res.partner"]
                    .sudo()
                    .search([("ref", "=", identifier)], limit=1)
                )

            @property
            def converter(self):
                return self._data.partner

            def schema(self):
                return self._schema._simple_record()

        class CurrencyFinder(Component):
            _name = "shopfloor.scan.currency.handler"
            _inherit = "shopfloor.scan.anything.handler"

            record_type = "testcurrency"

            def search(self, identifier):
                return (
                    self.env["res.currency"]
                    .sudo()
                    .search([("name", "=", identifier)], limit=1)
                )

            @property
            def converter(self):
                return lambda record: record.jsonify(
                    self._data._simple_record_parser(), one=True
                )

            def schema(self):
                return self._schema._simple_record()

        return (PartnerFinder, CurrencyFinder)

    def test_scan(self):
        service = self.get_service("scan_anything")
        test_handlers = self._get_test_handlers()

        for finder_class in test_handlers:
            finder_class._build_component(service.work.components_registry)

        handlers = service._scan_handlers()
        for handler_cls in test_handlers:
            self.assertIn(handler_cls._name, [x._name for x in handlers])

        record = self.env.ref("base.res_partner_4").sudo()
        record.ref = "1234"
        rec_type = "testpartner"
        identifier = record.ref
        data = record.jsonify(["id", "name"], one=True)
        self._test_response_ok(
            rec_type, data, identifier, record_types=("testpartner", "testcurrency")
        )

        record = self.env.ref("base.EUR").sudo()
        rec_type = "testcurrency"
        identifier = record.name
        data = record.jsonify(["id", "name"], one=True)
        self._test_response_ok(
            rec_type, data, identifier, record_types=("testpartner", "testcurrency")
        )

    def test_scan_error(self):
        self._test_response_ko(
            "404-NOTFOUND", record_types=("testpartner", "testcurrency")
        )
