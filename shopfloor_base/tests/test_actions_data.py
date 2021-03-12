# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from .common import CommonCase
from .common_misc import ActionsDataTestMixin


class ActionsDataCase(CommonCase, ActionsDataTestMixin):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.partner = cls.env.ref("base.res_partner_12").sudo()

    def test_data_partner(self):
        data = self.data.partner(self.partner)
        self.assert_schema(self.schema._simple_record(), data)
        self.assertDictEqual(
            data, {"id": self.partner.id, "name": self.partner.display_name}
        )
