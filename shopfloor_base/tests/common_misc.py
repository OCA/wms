# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from .common import CommonCase

_logger = logging.getLogger(__name__)


try:
    from cerberus import Validator
except ImportError:
    _logger.debug("Can not import cerberus")


class ActionsDataCaseBase(CommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.partner = cls.env.ref("base.res_partner_12")

    def assert_schema(self, schema, data):
        validator = Validator(schema)
        self.assertTrue(validator.validate(data), validator.errors)


class CommonMenuCase(CommonCase):
    @classmethod
    def setUpClassVars(cls, *args, **kwargs):
        super().setUpClassVars(*args, **kwargs)
        cls.profile = cls.env.ref("shopfloor_base.profile_demo_2")

    def setUp(self):
        super().setUp()
        with self.work_on_services(profile=self.profile) as work:
            self.service = work.component(usage="menu")

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
            "scenario": menu.scenario,
        }
        return data
