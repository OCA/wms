# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from freezegun import freeze_time

from odoo.addons.stock_release_channel.tests.common import ChannelReleaseCase


def _do_picking(picking):
    for move in picking.move_ids:
        move.quantity_done = move.product_qty
    picking._action_done()


class TestStockReleaseChannelShipmentAdviceDate(ChannelReleaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.tz = "UTC"
        cls.channel.shipment_planning_method = "simple"
        output_loc = cls.channel.picking_ids.move_ids.location_id
        cls._update_qty_in_location(output_loc, cls.product1, 100)
        cls._update_qty_in_location(output_loc, cls.product2, 100)
        cls.channel.picking_ids.move_ids.write({"procure_method": "make_to_stock"})
        cls.channel.picking_ids.action_assign()

    @freeze_time("2023-04-01 12:00:00")
    def test_00(self):
        """
        Test planned arrival and departure datetime.
        If the scheduled time is later than the current time, the date will be
        considered today.
        if the scheduled time is earlier than the current time, the date will be
        considered tomorrow.
        """
        self.channel.planned_arrival_time = 10
        self.channel.planned_departure_time = 11
        self.assertEqual(
            self.channel.planned_arrival_datetime, datetime(2023, 4, 2, 10)
        )
        self.assertEqual(
            self.channel.planned_departure_datetime, datetime(2023, 4, 2, 11)
        )
        self.channel.planned_arrival_time = 14
        self.channel.planned_departure_time = 16
        self.assertEqual(
            self.channel.planned_arrival_datetime, datetime(2023, 4, 1, 14)
        )
        self.assertEqual(
            self.channel.planned_departure_datetime, datetime(2023, 4, 1, 16)
        )

    @freeze_time("2023-04-01 12:00:00")
    def test_01(self):
        self.channel.planned_arrival_time = 10
        self.channel.planned_departure_time = 11
        shipment_advices = self.channel._plan_shipments()
        self.assertTrue(shipment_advices)
        self.assertEqual(shipment_advices.arrival_date, datetime(2023, 4, 2, 10))
        self.assertEqual(shipment_advices.departure_date, datetime(2023, 4, 2, 11))
