# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.shopfloor.tests.test_actions_data_base import ActionsDataDetailCaseBase


class ActionsDataDetailManufCaseBase(ActionsDataDetailCaseBase):
    def _expected_product_detail(self, record, **kw):
        res = super()._expected_product_detail(record, **kw)
        if kw.get("full"):
            res["manufacturer"] = (
                {
                    "id": record.manufacturer_id.id,
                    "name": record.manufacturer_id.name,
                }
                if record.manufacturer_id
                else None
            )
        return res
