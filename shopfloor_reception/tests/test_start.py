# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from freezegun import freeze_time

from odoo import fields

from .common import CommonCase

_YESTERDAY = "2022-12-05"
_TODAY = "2022-12-06"
_TOMORROW = "2022-12-07"


@freeze_time(_TODAY)
class TestStart(CommonCase):
    def test_domain_stock_picking(self):
        dates = (_YESTERDAY, _TODAY, _TOMORROW)
        pickings = {}
        for date in dates:
            for _i in range(1, 4):
                picking = self._create_picking(scheduled_date=date)
                pickings.setdefault(date, []).append(picking)
        domain = self.service._domain_stock_picking(today_only=True)
        pickings_due_today = self.env["stock.picking"].search(domain)
        self.assertEqual(len(pickings_due_today), 3)
        for picking in pickings_due_today:
            self.assertEqual(picking.scheduled_date, fields.Datetime.today())

    def test_start(self):
        response = self.service.dispatch("start")
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": []},
        )
        # Create a picking due today
        picking_due_today = self._create_picking()
        picking_due_today.write({"scheduled_date": _TODAY})
        # Create a picking due tomorrow
        self._create_picking().write({"scheduled_date": _TOMORROW})

        # Only the one due today will be returned in the first page
        response = self.service.dispatch("start")
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": self._data_for_pickings(picking_due_today)},
        )
