# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.shopfloor.tests.test_actions_data_base import ActionsDataCaseBase


class InventoryActionsDataCaseBase(ActionsDataCaseBase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.inventory = (
            cls.env["stock.inventory"]
            .sudo()
            .create(
                {
                    "location_ids": [(6, 0, cls.stock_location.ids)],
                    "prefill_counted_quantity": "zero",
                }
            )
        )

    def _expected_inventory(self, record, **kw):
        data = {
            "id": record.id,
            "name": record.name,
            "location_count": record.location_count,
            "remaining_location_count": record.remaining_location_count,
            "inventory_line_count": record.inventory_line_count,
        }
        return data
