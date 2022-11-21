# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import datetime

from odoo import fields

from .common import CommonCase


class TestManualSelection(CommonCase):
    def test_list_stock_pickings(self):
        response = self.service.dispatch("list_stock_pickings")
        self.assert_response(
            response,
            next_state="manual_selection",
            data={"pickings": []},
        )
        # Create a picking due today
        today = fields.Datetime.today()
        picking_due_today = self._create_picking()
        picking_due_today.write({"scheduled_date": today})
        # Create a picking due tomorrow
        tomorrow = today + datetime.timedelta(days=1)
        picking_due_tomorrow = self._create_picking()
        picking_due_tomorrow.write({"scheduled_date": tomorrow})

        # Both pickings will be returned
        response = self.service.dispatch("list_stock_pickings")
        pickings = self.env["stock.picking"].browse(
            [picking_due_today.id, picking_due_tomorrow.id]
        )
        self.assert_response(
            response,
            next_state="manual_selection",
            data={"pickings": self._data_for_pickings(pickings)},
        )
