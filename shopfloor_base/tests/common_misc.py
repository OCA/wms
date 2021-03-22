# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import logging

_logger = logging.getLogger(__name__)


try:
    from cerberus import Validator
except ImportError:
    _logger.debug("Can not import cerberus")


class ActionsDataTestMixin(object):
    def assert_schema(self, schema, data):
        validator = Validator(schema)
        self.assertTrue(validator.validate(data), validator.errors)


class MenuTestMixin(object):
    def _get_service(self, profile=None):
        with self.work_on_services(profile=profile or self.profile) as work:
            return work.component(usage="menu")

    def _assert_menu_response(self, response, menus, **kw):
        self.assert_response(
            response,
            data={
                "size": len(menus),
                "records": [self._data_for_menu_item(menu, **kw) for menu in menus],
            },
        )

    def _data_for_menu_item(self, menu, **kw):
        data = {
            "id": menu.id,
            "name": menu.name,
            "scenario": menu.scenario_id.key,
        }
        return data


class OpenAPITestMixin(object):
    def _test_openapi(self, **kw):
        with self.work_on_services(**kw) as work:
            components = work.many_components()
            for comp in components:
                if getattr(comp, "_is_rest_service_component", None) and comp._usage:
                    # will raise if it fails to generate the openapi specs
                    comp.to_openapi()


class ScanAnythingTestMixin(object):
    def _get_service(self):
        with self.work_on_services() as work:
            return work.component(usage="scan_anything")

    def _test_response_ok(self, rec_type, data, identifier, record_types=None):
        service = self._get_service()
        params = {"identifier": identifier, "record_types": record_types}
        response = service.dispatch("scan", params=params)
        self.assert_response(
            response, data={"type": rec_type, "identifier": identifier, "record": data},
        )

    def _test_response_ko(self, identifier, record_types=None):
        service = self._get_service()
        tried = record_types or [x.record_type for x in service._scan_handlers()]
        params = {"identifier": identifier, "record_types": record_types}
        response = service.dispatch("scan", params=params)
        message = response["message"]
        self.assertEqual(message["message_type"], "error")
        self.assertIn("Record not found", message["body"])
        for rec_type in tried:
            self.assertIn(rec_type, message["body"])
