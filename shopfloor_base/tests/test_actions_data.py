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
        cls.partner = cls.env.ref("base.res_partner_12").sudo()

    def assert_schema(self, schema, data):
        validator = Validator(schema)
        self.assertTrue(validator.validate(data), validator.errors)


class ActionsDataCase(ActionsDataCaseBase):
    def test_data_partner(self):
        data = self.data.partner(self.partner)
        self.assert_schema(self.schema._simple_record(), data)
        self.assertDictEqual(data, {"id": self.partner.id, "name": self.partner.name})
